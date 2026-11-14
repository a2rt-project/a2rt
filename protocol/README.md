# A2RT：智能体实时多模态交互协议

**Agent-to-Real-Time Protocol**。版本：**0.2 草案**；日期：2026-11-15；线协议标识：`a2rt/0.2`。

A2RT 定义智能体与环境之间的事件、媒体、观察和执行反馈。各轨道独立产生数据；反馈立即交付当前已就绪的信息，不等待视觉、听觉、状态和操作结果全部就绪。事件与反馈保留因果关系，音频、画面和操作不必同频。

本目录是独立的通用协议草案。核心不绑定项目名、画布、Excalidraw、模型厂商或 MCP 服务，不是生产 SDK。[Canvas Profile](./profiles/canvas/README.md) 和[六轨验证网页](../../../benchmarks/canvas_event_loop/README.md) 已适配 A2RT 0.2；原 [canvas-ai-event-loop](../canvas-ai-event-loop/README.md) 保留为历史协议，旧录制与新消息不可混用。

## 阅读顺序

| 文档 | 内容 |
| --- | --- |
| [01-core-and-profiles.md](./01-core-and-profiles.md) | 通用核心、环境 Profile、身份、事件与工具扩展 |
| [02-tracks-and-time.md](./02-tracks-and-time.md) | 六条逻辑轨道、独立更新、空数据与历史引用、时钟与音频 |
| [03-feedback-loop.md](./03-feedback-loop.md) | 异步事件与反馈、Profile 执行策略、在途窗口与独立轨道更新 |
| [04-execution-and-recovery.md](./04-execution-and-recovery.md) | 操作互斥、执行回执、取消、超时、重连、背压和录像 |
| [05-wire-and-validation.md](./05-wire-and-validation.md) | 消息字段、示例、校验方法及后续工程验收 |
| [profiles/canvas/README.md](./profiles/canvas/README.md) | Canvas 领域绑定、每 actor 单任务、选区、独立反馈及 mock 实现 |

## 六条逻辑轨道

| 标准标识 | 名称 | 生产方与内容 |
| --- | --- | --- |
| `assistant.audio` | assistant 音频轨 | 模型语音、显式静音、音频缺口 |
| `assistant.events` | assistant 事件轨 | 模型操作请求、工具调用、空事件 |
| `environment.audio` | 环境音频轨 | 人、其他参与者、应用或设备产生的声音 |
| `environment.events` | 环境事件轨 | 人或其他来源已经发生的操作和系统事件 |
| `environment.visual` | 环境画面轨 | 截图、视频帧或其他协商过的视觉表示 |
| `environment.state` | 环境状态与结果轨 | 执行回执、结构化领域状态、播放进度及覆盖缺口等 |

轨道是信息分类，不是六个连接、六个等长数组或六份重复消息。一条轨道可以有多个具名 stream，例如多个麦克风、多台摄像机、多个状态命名空间。按会话能力启用；没有视觉的环境仍可使用 A2RT。基础闭环必须注册 `assistant.events`，以及 `environment.state` 中分别承载事件回执 `core.result` 和控制响应 `core.control_result` 的 stream。

## 不可破坏的约束

1. 双向使用同一个 Event 定义。发送方向、参与者身份和“请求／已发生事实”分别表达。
2. 每个模型决策输出恰好一个事件；没有操作时使用 `core.noop`。音频不再是每个决策的必填窗口。
3. 核心不强制“一个 output 等待一个 feedback”。Profile 声明执行策略，会话选择后冻结；反馈关联事件，不充当全局决策许可。
4. 环境可主动发布轨道更新；模型可独立发送音频分块。回执可以异步或批量交付，不重放历史动作。
5. 活动操作数与未获回执的事件数分别限制。具体上限与作用域由 Profile 定义；同一次操作可以包含多个在途事件。`noop` 和声音不新建操作。
6. 空、未知、静音、历史引用与丢失含义不同。历史画面不得伪装为当前采集；历史音频不得重复消费。
7. 各数据保留来源时刻和版本。反馈发送时刻只是交付时刻，不是全部模态共同的采集时刻。
8. 只有声明的依赖需要同步。例如某动作必须对齐某段音频，则局部等待相关依赖；不把此等待扩大到全会话。
9. 执行器产生真实结果，模型不能自证成功；超时表示未确认，不能据此重复执行有副作用的操作。
10. 保存、录像和数据库提交不阻塞实时执行及观察。

## 通用性与稳定性

核心固定生命周期、时间、来源、回执和扩展入口；Profile 定义领域事件、状态及执行策略，适配器完成真实执行。事件、工具、状态 Schema 和策略清单随会话冻结并带内容哈希。可扩展不等于接受未经协商的任意 JSON。

0.2 移除 0.1 的 after_reply 决策许可，round_id 改为 output_seq；reply_to 仅关联请求，允许同一请求获得多次进展反馈。清单新增所选 execution_policy_id。属于不兼容的草案修订，不能将旧录制只替换版本号后作为新协议使用。

本版没有硬实时截止保证，不固定 10 fps、100 ms 窗口或音频采样率。处理时延不同是设计输入；实际可达到的响应时间、吞吐和同步误差属于下一步工程验收。

## 本次交付

`schemas/` 固定草案的结构；`examples/` 使用**非画布的计数器环境**演示音频先到、视觉迟到、工具运行中，以及一个操作连续发送多个事件、随后批量反馈。运行：

```sh
python3 protocol/validate_examples.py
```

该校验覆盖通用文档结构、示例因果关系和关键反例。Canvas 的受限 mock、双场景录制、原生渲染和独立轨道回放另有 [Canvas 校验](../../../benchmarks/canvas_event_loop/README.md#校验)，仍不宣称已经连接真实模型、MCP 或真实网络。生产采集与协作接入边界见适配评估。
