# Canvas Realtime Profile：当前 A2RT 的六轨验证实例

状态：可运行的本地 mock，Profile `canvas.excalidraw.realtime` / `0.3.0-draft`，2026-11-16。

本目录独立验证当前 A2RT 的「根时钟 → 子时钟 → 信息同步组 → 轨道」设计。它不修改 A2RT Core，也不为 Core 宣布新线协议版本。`canvas.a2rt.mock.v2` 是本实例的二进制 Binding 标识；任务、工具、反馈完整性、播放和恢复规则均由这个 Canvas Profile 定义。交互信息时钟为 10Hz，发送端组织观察，接入层校验后开放给模型，重同步由运行时执行。验证范围仍限于本地 mock。

- [Profile 配置](./profile.json)：工具能力、事件类别、任务限制和恢复规则。
- [会话配置](./session.json)：时钟树、同步组、格式与七条协议轨道。
- [交互和交付契约](./01-interaction-and-delivery.md)：时间关系、反馈、任务与异常规则。
- [二进制音频 Binding](./02-binary-binding.md)：真实 PCM、HTTP 流、封装、容量、去重与解码。

## 三组角色、六条业务轨道

方向以模型为参照；只有轨道定义角色和方向。

| 展示分组 | track_id | role | direction | 内容 |
| --- | --- | --- | --- | --- |
| assistant | `assistant.audio` | assistant | output | 讲解音频的 L16 字节、采样窗口及操作依赖 |
| assistant | `assistant.events` | assistant | output | 指针事件、工具调用、空事件和本次输出结束 |
| user | `user.audio` | user | input | 用户麦克风的 L16 字节，按观察截止点切片 |
| user | `user.events` | user | input | 用户的同构指针／工具事件，包含已执行事实 |
| environment | `environment.visual` | environment | input | 当前画布画面对应的冻结场景 |
| environment | `environment.state` | environment | input | 场景、选中元素／组 ID、工具状态、执行结果、播放进度 |

以上六轨绑定 `canvas_interaction` 信息同步组。`user.audio` 和 `user.events` 明确表示用户。

另有且仅有一条 `role=system`、`direction=input` 的 `system` 轨道，绑定独立的 `system_notifications` 同步组。它由可信协调器通知会话和异常状态，在网页「系统 / 运行时」面板显示，不计入六条业务轨道。本次输出结束通知在 assistant 输出轨道中；传输恢复不生成 assistant 事件，运行时日志也不构成新增轨道。

异常处置是本 Profile 的选择：超时观察过期隔离、迟到旧画面不再交付，协调器通过 system 发布约定的超时、恢复或暂停通知。这些通知是符合 Canvas 契约的轨道内容；A2RT Core 不强制它们，也不要求通用错误控制消息。其他 Profile 可选择直接丢弃、自定义通知轨道或另建通知通道，参见[职责边界 §1.3](../../03-core-profile-responsibilities.md#13-默认业务通道与异常处置)。本实例未因此新增轨道或传输接口。

## 演示行为

正常演示包含 240 个交互单元、24 秒语音窗口、双方原生协作光标、选中框与锚点、绘制、拖动、框选、对齐、分组、擦除、取消以及非法插入拒绝。鼠标样式不随工具变更，工具状态以 JSON 表达。画面使用原生 Excalidraw 渲染，不自行重画工具图标或协作光标。

每个 actor 同时最多一个 task；双方各自的 task 可以并行。普通 assistant 事件以完整观察为推进门槛，user 本地操作不等待模型反馈。音频可与该 actor 的操作同时进行。没有对象锁；这个 mock 以确定的事件到达顺序执行，仅覆盖这里声明的演示范围，不声称实现完整 Excalidraw 协作冲突算法或全部编辑工具。

故障演示保持等待、超时恢复、迟到丢弃和暂停语义。延迟到达不会改写原采集时间；新观察和下一操作分别进入合法的 100ms 信息周期，避免同轨同周期发布第二份状态。故障模式总时长为 24.500 秒，正常模式为 24.000 秒且节奏逐帧一致。恢复与后续操作遵守 10Hz 周期约束，详见[交互和交付契约](./01-interaction-and-delivery.md#4-超时与恢复)。

## 实现范围

源码项目中的验证网页是可检查、可导出、可回放的本地 mock；官网发布当前契约与机器文件，不托管该演示程序。AI 和 user 行为为 mock，语音以服务端 TTS WAV 模拟来源，实际逐段发送 audio/L16 字节。网页按实时节拍接收后，从接收缓存解码播放。JSON 场景经过原生 Excalidraw 解码成画面，未伪装成已经编码传输的视频。音频经过真实本地 HTTP 二进制流；它不连接真实模型、不打开麦克风、不写业务数据库，不提供生产 WebSocket／RTC 服务。本地传输测试不能直接用作公网性能结论。

## 模型消费边界

本实例落实[职责边界 §1.2](../../03-core-profile-responsibilities.md#12-面向模型的信息交付边界)：

- 谁发送谁负责：环境侧负责观察的准备与发送侧恢复，模型服务及其适配器负责输出音频和操作的组织与发送侧恢复；双方接收端验收、按约定报告问题，再消费或执行合格内容。接收重组不转移发送端的信息准备责任。
- `root` 为 1,000Hz，`interaction` 为 10Hz；独立通知时钟仍为 100Hz，用于及时发布系统通知，不要求模型每 10ms 作一次业务决策。内部重试的 20ms 不改变交互时钟。
- 发送端在传输前组织并校验同版本画面、状态、音频与事件；共享的模型接入器逐包接收后确认完整性，去重并隔离过期观察。实际 HTTP 接收也使用该接入器，可逐窗触发就绪回调；网页等到整段接收完成才开放任意回放。
- 观察超时由环境侧协调器的 `RecoveryRuntime` 自动处理，负责在合法周期重新采集并交付观察；`ModelIngress` 负责接收验收与过期隔离。失败则按 Profile 暂停决策并清理任务。assistant 等待符合契约的新观察，不生成传输恢复事件。

当前 Profile 为 `0.3.0-draft`，会话配置声明并校验 `profile_version`。Binding 标识为 `canvas.a2rt.mock.v2`，不代表 A2RT Core 的线协议版本。

网页用于逐帧检查的传输信息不全部进入模型内容。当前没有真实模型；视觉采用 Excalidraw 场景解码，真实模型接口需要图片／视频时，还须接入相应渲染编码适配器。故障时序由确定性调度器模拟，本地验证不代表已经实现生产重连、跨设备时钟同步或公网恢复服务。
