# 通用核心、能力清单与环境扩展

## 1. 分层

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| A2RT Core | 消息、轨道更新、身份引用、时钟、事件、操作边界、回执和恢复 | 图形、页面、控件、文件等领域对象含义 |
| Environment Profile | 自定义事件、状态、执行策略、并发上限、依赖屏障及一致性规则 | 改写核心回执、幂等或身份规则 |
| Adapter | 将声明能力映射到真实应用／设备；获取真实观察 | 依据模型请求虚构已执行结果 |
| Binding | 可靠消息交付、媒体资源寻址、鉴权、连接与流控 | 决定业务操作是否成功 |

画布可定义 Canvas Profile；网页、桌面、仿真环境可定义其他 Profile。核心不含 `element_ids`、`group_ids`、选区、画笔、视口、`render_seq` 或 Excalidraw 版本。

## 2. 会话清单与身份

初始化先协商清单，再发布 `feedback_seq=0` 的初始反馈 F0。消息引用同一 session_id、epoch 和 manifest_id；epoch 内清单不可变。清单至少列出：

- 协议版本与 Profile 的 ID、版本、内容 SHA-256；示例包的 schema_ref 是包内相对路径，生产 binding 须规定可解析资源机制。
- 可信来源注册表：source_id、actor_id、角色与环境上下文 context_id；一个 actor 可有多个传感器来源。
- stream_id、所属逻辑轨道、唯一 source_id、格式及其时钟；同一逻辑轨道可容纳多个 stream。
- 自定义事件的 payload Schema、允许的 operation phase；工具的服务绑定、原始 name、inputSchema 和执行属性。
- 领域状态 Schema，媒体编码参数、资源大小上限、反馈等待和停滞超时、队列上限等。
- Profile 中具名的 execution_policies，以及每个 context 选择的 execution_policy_id；不能由模型在每条消息中临时修改策略。

角色可为 `assistant/user/agent/system`。环境是这些来源的集合，不是把所有来源改名为 user。A2RT 消息用 `sender=assistant/environment` 标识方向；厂商适配器可把环境反馈映射为模型接口中的 user 或 tool 消息，但不能改掉原始 actor_id 和 source_id。

消息内的身份只是引用。绑定层必须把连接鉴权主体绑定到获准的 source、actor、context 和能力；不能允许模型通过填写字符串越权。清单描述“支持什么”，授权和当前状态还要决定“这次允许做什么”。

清单、身份绑定或 Profile Schema 改变时，在旧操作清理／对账后开启新 epoch，并重新发布清单及 F0。旧命令不得自动重放。

## 3. 双向统一 Event

Event 的核心字段：

| 字段 | 意义 |
| --- | --- |
| event_id | epoch 内唯一，重传保留 ID 与内容 |
| actor_id / context_id | 谁产生事件、作用于哪个已注册环境上下文 |
| time | 来源采集／产出时刻：clock_id + 整数 t_us；不等于执行时刻 |
| operation_id / phase | 操作边界；phase 为 begin/update/end/cancel/single/none |
| type | 带命名空间的事件类型；核心保留 core.* |
| payload | 按固定能力清单的 Schema 校验 |
| timing | immediate 或明确音频采样位置，用于请求的呈现调度 |

发送到 `assistant.events` 是执行请求。`environment.events` 中的同一个 Event 结构是**已发生事实**，以 `{event, disposition: "observed"}` 承载，不能送回执行器再执行。一个输入造成的对象变化属于结果／状态，不能再伪造第二条命令。

已观察事件的 timing 固定为 immediate，time 是实际来源时刻；如果原请求具有音频调度要求，原 Event 保留在请求日志中，实际执行时刻写入回执，而不是另造一次环境输入。

## 4. 核心事件与扩展事件

核心只保留：

- `core.noop`：payload={}、operation_id=null、phase=none、timing=immediate。明确没有新操作，不释放已有操作，不等于静音、丢包或环境无变化。
- `core.tool_call`：payload={server_id, name, arguments}、非空 operation_id、phase=begin。调用结果和终态由执行器回执表达，不需要模型再发送“工具结束”。

例如 `example.counter.increment` 或未来的 `canvas.pointer` 都是 Profile 注册的类型。未声明的类型不能因通过通用 Event Schema 就被执行。`core.*` 不允许 Profile 自行扩展。

两层验证：核心封装 → 清单中的事件／工具参数 Schema；之后仍须检查状态、权限、操作互斥和目标依赖。训练配置固定清单哈希，模型可使用的事件集合因此是确定的；不同环境可拥有不同集合。

## 5. 连续操作

`begin → update* → end/cancel` 表达跨多个事件的一个操作；`single` 表达单事件操作。operation_id 用于并发计数、状态关联和清理，不是待执行计划，不含 steps、duration_ms 或预先计算的终点。允许在途事件时，这些事件不必各自等待上一条回执，但执行器必须按操作内顺序应用。

Profile 声明具体开始／更新／结束事件及清理义务。指针 Profile 可以将 down/move/up/cancel 映射到这些阶段；核心不要求所有环境都存在鼠标。`end` 是正常收尾请求，只有执行器完成正常收尾及释放资源后才终结；`cancel` 清理活动输入，但不自动回滚已发生副作用。

核心不固定“一次一个操作”。Profile 的 max_active_operations 与 operation_scope 决定上限和范围；Canvas 建议使用 actor 范围、上限 1，限制横跨该 actor 的上下文，不能换画板绕过。其他 Profile 可明确允许更大并发。不同 actor 独立计数；跨 actor 冲突由 Profile 与真实应用协调，核心不内置对象锁。

Profile 的 execution_policies 是 policy_id 到策略对象的映射，结构见 [execution-policy.schema.json](./schemas/execution-policy.schema.json)。所选策略和领域前置条件必须一起验证。单任务不等于单事件在途，详见 [执行策略与异步反馈](./03-feedback-loop.md)。

## 6. 工具调用

保留工具原始 name 和 arguments；server_id 映射清单中可信服务，禁止模型传任意执行 URL。实际 MCP JSON-RPC ID、握手和鉴权由适配器处理，event_id 负责 A2RT 的去重与结果关联。具备相同 name 的工具以 server_id 区分。

工具能力声明：参数 Schema、结果 Schema（若有）、作用上下文、只读／修改、副作用可见性、atomic/incremental 呈现能力、取消及去重能力。依赖选区、显式对象 ID 或当前窗口等条件写入 Profile 的绑定规则，不固定在核心枚举中。

MCP 是可选的工具接入方式，本地适配器也能实现 core.tool_call。A2RT 不是 MCP、NLIP 或某个模型 API 的别名；后续可定义映射，但不能仅封装一次 JSON 就宣称完全兼容这些协议。
