# 交互、时钟与同步交付

本章的事件名、任务 ID、工具名和恢复状态均为 Canvas Profile 定义，不是 A2RT Core 标准事件。

本章定义 `0.3.0-draft` 的交互和交付契约：10Hz 信息节拍、发送端预处理、接入层完整性检查和运行时恢复，职责依据见[发送端预处理与模型消费边界](../../03-core-profile-responsibilities.md#12-面向模型的信息交付边界)。本地 mock 的实现范围见 [README](./README.md#模型消费边界)。

## 1. 时钟和同步组

会话 epoch 内的 `root` 固定为 1,000Hz；每个根周期 1ms，标准逻辑单位 1,024 字节。`interaction` 以 `period_parent_ticks=100` 派生，信息周期为 100ms、更新节拍为 10Hz。`notifications` 保持 `period_parent_ticks=10`，独立通知周期为 10ms、100Hz。两者 `offset_parent_ticks=0`。六轨属于 `canvas_interaction`，system 属于 `system_notifications`；两个同步组独立交付。

交互信息节拍与普通事件的每 100ms 一次一致；音频采样率仍为 24kHz。细根刻度用于计量和调度，不要求模型每 1ms 或每个系统通知周期做一次业务决策；空闲周期无需强制发包。网页“第几帧”表示已完成交互单元的序号，`frame_seq` 是信息同步组的周期号。正常模式网页第 1 帧对应 `frame_seq=1`；故障等待期间周期继续前进，二者可能不同。

内部重试可以使用 20ms 的计时器，完成后等待合法交互周期发布新的观察；它不改变 10Hz 信息时钟，也不生成模型侧恢复请求。

根刻度与可见播放时间的映射为：

```text
root_tick = visible_time_ms + 100
frame_seq = root_tick / 100  （交互组仅在合法周期起点采集）
root_window = [frame_seq × 100, (frame_seq + 1) × 100)
```

预滚窗口 `[0,100)` 承载初始场景与空音频；可见播放时间 0ms 从 root=100 开始。初始观察与第一条操作后的观察分别占据不同周期，可见演示仍从 0ms 开始、正常播放长度仍为 24 秒。信息窗口标识发布位置，媒体覆盖区间由载荷单独声明：普通 assistant 音频覆盖接下来的 100ms，反馈 user 音频覆盖上一成功交付截止点至本次截止点。

## 2. 每个 actor 一个 task

user 和 assistant 的领域事件使用相同结构：`event_id`、`actor_id`、`context_id`、`task_id`、`phase`、`type`、`payload`、`timing`、`time`。输入事实外层可带 `disposition=observed`；assistant 普通输出外层带 `basis_observation_id`，指向最后一次已完整交付的观察。

| type | 任务规则 | 载荷 |
| --- | --- | --- |
| `canvas.pointer` | down/begin 开始；move/update 继续；up/end 或 cancel/cancel 结束；无按键的 move/single 是单次移动 | 接近 Pointer Events 的 name、pointer_id、pointer_type、x/y、button、buttons、scene 坐标空间 |
| `canvas.tool_call` | 一次工具调用占一个 task；本 mock 同步完成 | `server_id`、`name`、`arguments`，匹配 Profile 的工具 Schema |
| `canvas.noop` | 不创建新 task，可以出现在指针任务的等待期 | 空 payload，task_id=null、phase=none |
| `canvas.output_end` | 结束本次输出，不自动结束会话 | output_id |

只有 `canvas.output_end` 使用事件轨的 `mode=control` 外层；指针、工具调用与 `canvas.noop` 使用 `mode=data`。传输恢复由运行时负责，不属于模型事件契约。操作任务期间不能插入该 actor 的第二个指针任务或工具任务。音频和空事件不占额外 task。user 与 assistant 各有一个名额，不共享全局单任务门槛，也不对对象加锁。

这里的 `mode=control` 是 Canvas 自定义的轨道载荷模式，仍占该事件轨本周期的一个数据帧位置；它不是 A2RT Core 定义的错误控制消息，也不是轨道外通知通道。

END/CANCEL 清理按键、捕获和 active_task_id，已终结 task 不允许再更新。相同 event_id 原样重传不重复执行；相同 event_id 改内容拒绝。异常情况下可信执行器可清理丢失 END 的任务。

Profile 的工具目录采用 MCP 风格 `name + inputSchema`，目前固定支持 `editor_set_tool`、`editor_set_style`、`editor_action`（alignTop、group），服务器名 `canvas-editor`。这是一组版本化 mock 能力，不冒充官方 MCP 服务或完整工具清单。工具调用中 actor 的选区是目标：状态反馈返回 element_ids、group_ids、bounds、selection.revision、可用能力和工具状态；依赖选区的 assistant 调用必须基于有效的完整观察。

## 3. 同步反馈与音频

环境端接收 assistant.events 与 assistant.audio；模型端接收 user.audio、user.events、environment.visual、environment.state。接收端仅等待适用于自身的成员，不等待反向轨道，也不等待独立 system 同步组。

两个方向均遵循“谁发送谁负责”：环境侧发送端对观察的拼装、对齐、发送前校验和发送侧恢复负责；模型服务及其适配器对输出音频、事件与时间关联的组织、发送前检查和发送侧恢复负责。接收端验收并按约定报告缺失或冲突，不猜测或修补发送内容的业务含义。环境执行后反馈实际结果时，又作为结果的发送端承担相应责任。

每次普通 assistant 操作执行后冻结快照，得到一个 revision、一个 cutoff_root_tick、完整场景和执行结果。环境状态中的结果、选区、播放状态是同一份状态载荷的字段，不拆成同轨同周期的多条数据帧。

模型可用观察满足：

1. 本周期四条输入轨都有一个数据帧；user.events 可为显式空帧。历史 user 事件保留原周期，在状态中通过 `user_event_refs` 引用，不能再次伪装成新事件。
2. visual 与 state 的 revision、cutoff_root_tick 及场景内容一致；截止点等于当前信息周期的起点。
3. user.audio 覆盖上次成功交付的截止点到当前截止点；预滚无音频，首个有效截止点为 root=100。区间连续且不重复消费；明确的 silence 是真实静音，未知／丢失音频不能冒充静音。
4. 所需数据已到齐。音频为真实收到的 L16 字节，字节数和样本范围必须匹配；视觉资源是冻结场景。真正图片／视频 Binding 还须校验解码就绪。

后端发送端在传输及故障注入前按这些规则组织并校验观察；共享的 `ModelIngress` 在 mock 调度和真实 HTTP 接收路径中逐包重组、去重、校验音频连续性与场景一致性，仅完整且未过期的观察触发就绪回调。当前网页用场景 JSON 渲染画面；真实模型接口需要图片／视频时，须再接入发送端渲染编码适配器，不能要求模型还原 Excalidraw 场景或修复传输。工具执行失败作为明确的业务结果可以出现在观察中。

assistant 每条普通输出携带 2,400 个样本，即 24kHz 单声道的 100ms 讲解。`timing.sample` 把操作绑定到该音频块的首样本；执行成功才按依赖播放。故意注入的非法工具事件不绑定讲解依赖，失败不阻止无关旁白。播放坐标与采样坐标分别保留，等待可导致播放停顿，但不会修改已产生的音频内容。

user 音频按完整观察截止点截取。例如两个快照相隔 200ms，该反馈携带 4,800 个样本，不能用“包传输了多久”反推音频长度；等待 180ms 到达的旧画面仍保留原采集截止点。音频帧头记录 `coverage`、`start_sample`、`sample_count`，二进制体包含对应样本；跨越 24 秒模拟源后的内容是本 mock 明确设定的静音，并以全零 PCM 字节实际传输。

可先收到回执和状态，但这些数据进入暂存区，不成为模型可见的完整观察。配套 visual 到达后组装并一次交付；没有再次发布一份“更新后的 state”。网页画面、选区和完整反馈 JSON 也一次切换。输出面板展示所选单元的原始输出；配置和系统面板分别用于检查会话定义和通知。

## 4. 超时与恢复

本节是 Canvas 选择的异常处置契约：不完整观察隔离、过期观察丢弃出交付流程，尝试运行时恢复，并由协调器通过 system 通知约定的状态变化。A2RT Core 不要求所有 Profile 使用这些事件、恢复次数或通知载体；其他 Profile 可以直接丢弃而不通知，或选择自定义轨道、另建通知通道等方式。内部机械性故障由运行时处理，模型只接收本 Profile 允许交付的观察和通知。

观察的补交或重新采集由环境侧发送运行时负责，接收层验收并维护缺失、过期与消费状态；恢复失败后的暂停和任务清理由协调器／执行器处理，不依赖模型产生恢复指令。本地 mock 将两端流程纳入同一确定性调度器：环境侧协调器的 `RecoveryRuntime` 持有观察期限与恢复状态，正常观察及时到齐则取消其超时任务；超时最多尝试一次恢复。`ModelIngress` 执行接收验收与隔离。网页将恢复日志显示在「系统 / 运行时」面板，不把它放入 assistant 事件流或新增轨道；这些本地流程不代表已经实现跨服务恢复控制通道。

`max_wait_root_ticks=300` 从操作后的首次暂存输入时计；`max_skew_root_ticks=0` 检查画面／状态截止点和版本、音频结束截止点。内容覆盖不等于网络到达时刻，对齐容差不允许舍入非法时钟边界。

- 48 号交互单元（网页第 49 帧）在可见时间 4,800ms 执行，画面晚 180ms。4,980ms 完整观察到齐，仍保留 4,800ms 的快照截止点；下一普通操作在合法周期 5,000ms 执行。
- 141 号单元（网页第 142 帧）在 14,200ms 执行，画面晚 600ms。14,500ms 运行时判定超时，释放待交付队列并将原周期标记过期，协调器通过 system 通知这个事实。
- 内部恢复准备于 14,520ms 完成，运行时等待到 14,600ms 的合法周期重新采集快照，使用新的周期和 revision，补齐未消费的 user 音频与事件引用。原操作不重新执行；期间没有 assistant 恢复事件或为恢复生成的空音频帧。
- 下一普通操作在 14,700ms 执行，与恢复观察隔一个 100ms 信息周期。14,800ms 迟到的旧 visual 保留原 frame_seq，只归档，不重新向模型交付。故障模式总长为 24,500ms；正常模式仍为 24,000ms。
- 持续故障中，运行时于 14,520ms 判定恢复失败并暂停 assistant 决策，system 通知；2,000 根刻度后执行器立即释放未结束的指针任务，其清理结果在下一个合法交互周期（16,600ms）由 environment.state 发布。缺画面时它不是完整观察，界面保留上一完整画面。user 本地行为继续，音频在合法的 100ms 周期持续传输到 24 秒；没有配套画面时不产生新完整观察。

控制通知或回执不能自动替代完整观察。超时不会伪造前一帧为当前画面。同步完整性与恢复都是本 Profile 的规则，不限制其他 A2RT Profile 使用不同交付方式。

## 5. 系统生命周期

唯一 system 输入轨道由协调器发布以下本 Profile 事件：session.started、observation.timeout、observation.recovered、session.suspended、task.cleaned、session.ended。Schema 位于本目录。系统只通知；服务端负责暂停、恢复和清理。通知不向其他同步组施加全局屏障。

assistant 的 `canvas.output_end` 说明本次输出完结；协调器的 `session.ended` 才说明此演示会话结束。两者不混用，也不定义成 A2RT Core 的通用模型事件。持久故障的会话保持 suspended，不伪造 session.ended。
