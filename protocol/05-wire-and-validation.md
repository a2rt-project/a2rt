# 消息结构、示例与校验

## 1. 公共消息头

所有消息包含 protocol=`a2rt/0.2`、kind、sender、session_id、epoch、manifest_id、message_id、sent_at。epoch 为非负整数，sent_at 为来源 clock_id/t_us。字段和枚举大小写敏感；除明确的 payload/value 扩展区外，不允许静默接受未知字段。

| kind | 额外字段 |
| --- | --- |
| output | output_seq（从 1 开始）、observed_feedback_seq、event、updates |
| feedback | feedback_seq（从 0 开始）、reply_to（output ID 或 null）、updates |
| media | updates，仅 assistant.audio |
| control | request_id、action（cancel/query/resync）、target、reason |

feedback 的 reply_to 非空时，updates 必须含该请求事件的 core.result；同一 output 可以被多次关联，例如先 accepted 后 completed。F0、独立观察和批量回执的 reply_to 可以为 null，具体结果始终按 event_id 关联。普通 feedback 不授予决策许可；仅某事件的首个真实回执释放其窗口占用。本版 control 由 assistant 侧可信协调器向环境发出，其权限由绑定检查；环境自主停止／清理通过主动反馈报告。

output.updates 可以为空，不要求附带音频。assistant.events 只有 output.event 这一个载体；media 不允许藏事件。feedback 只能携带 environment.* 更新。

## 2. 内容格式与清单

`schemas/message.schema.json` 定义消息及 TrackUpdate；`schemas/event.schema.json` 定义 Event；`schemas/manifest.schema.json` 定义会话清单。`schemas/execution-policy.schema.json` 定义 Profile 中的具名策略；每个 context 的 execution_policy_id 必须指向所属 Profile 声明的策略。完整性仍依赖跨消息检查和领域 Schema。

核心 stream.format：

| format | 允许轨道 | new.data |
| --- | --- | --- |
| core.audio | assistant.audio / environment.audio | 采样区间、媒体／静音、requires_events |
| core.event_record | environment.events | event、disposition=observed |
| core.result | environment.state | Event 执行结果 |
| core.playback | environment.state | stream_id、played_sample、buffered_until_sample、state |
| core.control_result | environment.state | request_id、revision、status、result、error |
| core.visual | environment.visual | ref、mime_type、width、height、source_state_refs |
| Profile 注册的状态 format | environment.state | schema_id、revision、value |

assistant.events 注册为 core.event，实际内容只在 output.event 中传递。core.playback 中 state 为 playing/paused/underrun/stopped；played_sample 是当前已呈现区间的排他末端，buffered_until_sample 是从该位置连续可播放缓存的排他末端，两者按对应音频流坐标计数。报告停播不会删除已经发生的播放。

清单包含 profile 的资源引用与 SHA-256。示例配置采用一个共同单调时钟、PCM16/24 kHz/单声道；这些是 fixture 的选择，不是 A2RT 通用限制。实现应校验资源哈希、两层 Schema、stream 来源绑定、clock 注册、媒体范围和操作状态。

## 3. 可复核示例

- [session.json](./examples/session.json)：非画布计数器环境的会话清单。
- [counter.profile.json](./examples/counter.profile.json)：自定义 increment/adjust 事件、set_value 工具、count 状态及可选执行策略。
- [async-session.json](./examples/async-session.json)：听觉先到、纯事件输出、独立 assistant 声音、工具运行中、状态先于视觉、历史画面引用、用户事件、无声继续操作及控制查询响应。
- [streaming-session.json](./examples/streaming-session.json)：一个活动操作的多条事件先发送，随后批量回执；user 独立操作，同一工具的多次关联反馈。

示例媒体使用 `example:` 占位引用，不包含可播放录音或可解码图像。媒体内容必须先就绪的约束在真实 binding 中验证；本示例只验证元数据。例子不依赖 Excalidraw，不暗示 Canvas Profile 已经完成。

这里的记录以消息到达顺序表示，**没有固定 fps 或等长 frames 数组**。示例的多个反馈之间不必插入 output；独立 media 不必附带 noop。

## 4. 文档校验

在仓库根目录运行（需要现有 Python jsonschema）：

```sh
python3 protocol/validate_examples.py
```

检查范围：Schema 合法性、清单哈希、策略选择、方向与来源、独立 stream 序号、音频范围、反馈关联、观察水位、事件窗口、活动操作数和历史引用。正例覆盖同操作多事件在途、批量回执、重复关联进展、其他 Profile 允许两个操作、视觉先于状态；反例覆盖 per_event 下提前发送、窗口溢出、操作数超限、end 后续接、回执关联错误等。媒体像素和实际资源就绪不由元数据校验器证明。

文档校验器是样例审查工具，不是生产执行器或全协议一致性测试；它验证消息和计数关系，没有实际驱动超时定时器、清理输入或播放音频。完整媒体校验、同步依赖环检测、跨服务幂等、实际时钟漂移、丢包恢复、资源鉴权和模型是否正确利用观察，属于后续工程验收。

## 5. 下一阶段验收场景

| 场景 | 应验证 |
| --- | --- |
| 音频先就绪，视觉延迟数轮 | 模型及时得到音频；视觉缺席不挡首个回执／下一次合法决策 |
| 视觉完全禁用 | 仅事件、状态及可选声音仍可运行 |
| 一直讲话，暂时无操作 | media 持续；不制造新操作或强制每块音频一个 noop |
| 一直操作，暂时无声音 | 无须合成静音；事件使用独立时间／immediate 调度 |
| 状态 r2 先到，r1 图像后到 | 模型知道图像来源，不覆盖新状态或伪称同一快照 |
| 相关声音与事件分开到达 | 仅关联片段等待，其他轨道继续；按实际播放时钟调度 |
| 工具 running 但无新 output | 实际完成后主动推送终态，不要求轮询 noop 才能看到 |
| 按下期间 cancel、断线或超时 | 输入状态清理，真实内容保留，对账旧副作用 |
| 多个用户／系统事件与 AI 并行 | 来源不混淆；按 Profile 协调，不能重新执行观察到的输入 |
| 同一操作连续发出多条事件 | 不逐条等待回执；执行顺序正确，名额与窗口分别计数 |
| 丢一条回执／窗口满／超时 | 剩余窗口可用；到限局部暂停；控制可达且有明确恢复或 suspended 结果 |
| 重传／迟到／重连 | 不重复执行、消费音频、释放窗口或复活旧操作 |
| 保存慢或失败 | 实时轨道继续，单独报告保存进度 |

分别测量首个反馈延迟、每轨采集到交付时间、实际事件应用时间、媒体同步误差和模型决策周期；不能只汇报一个“帧耗时”。
