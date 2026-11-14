# 异步事件、独立反馈与 Profile 执行策略

## 1. 三个独立过程

1. **环境采集与呈现持续运行**：用户、其他参与者、设备和应用独立产出音频、事件、画面和状态。
2. **模型按所选策略发送事件**：每个 output 含一个事件；是否等待上一条回执由 Profile 决定，不是 Core 的统一要求。
3. **轨道数据随就绪交付**：环境可主动补充反馈，assistant 可独立发送音频 media，不等待下一条操作或全部模态。

因果关系不等于逐条往返。事件与结果始终关联，但两条 output 之间可以没有 feedback，两条 feedback 之间也可以没有 output。连续事件按当前状态逐点生成，不需要恢复成预先给定终点和 duration_ms 的计划段。

## 2. 消息、顺序与观察水位

初始化清单生效后发布 F0：feedback_seq=0、reply_to=null。F0 只确认会话可用，可仅有状态或空模态，不要求全部传感器就绪；它不是可反复消耗的决策许可。

| 消息 | 规则 |
| --- | --- |
| output | output_seq 从 1 连续递增；event 恰好一条；updates 可为空或携带 assistant.audio；不含 after_reply |
| feedback | feedback_seq 从 0 连续递增；updates 携带已就绪的观察或回执；与 output 不要求一对一 |
| feedback.reply_to | 可为某已发送 output 的 ID，必须包含对应事件的真实回执；同一个 output 可有多次进展反馈。批量回执或独立观察可以为 null |
| media | assistant.audio 的独立分块，不占事件在途窗口或活动操作名额 |
| control | 取消、查询、恢复，不在普通事件窗口或操作队列后等待 |

output_seq 是事件轨的发送顺序，不是决定次数或视频帧号。feedback_seq 是环境交付顺序，不是采集顺序。重传保持 message_id、序号与内容不变，不重复执行或释放窗口名额。

observed_feedback_seq 表示这次输出所依据的、已连续交付给模型的反馈前缀，范围为 0 到已交付水位。多个连续 output 可以使用相同水位；异步输入继续到达时，不强行改写已经生成的输出。这个字段不是 ACK，不解锁窗口，也不声称模型理解了全部模态。

接收方按每个 operation 的发送顺序应用事件。先到的 end 请求必须排在之前 update 后面执行，不能因为 feedback 尚未返回就将顺序关系误解成“未执行”。Profile 可另行规定跨操作顺序及领域依赖。

新的环境更新不自动使在途输出失效。执行器检查 Profile 规定的目标、状态版本和坐标映射；无关音频多来一块不能让全部命令失效。需要选区 ID 等结果的动作，由 Profile 定义依赖屏障，确认真实结果后才生成或执行。

## 3. 两个独立限制

Profile 的 execution_policies 声明允许的完整策略；清单的 contexts[].execution_policy_id 选择其中一项。策略对象由 [execution-policy.schema.json](./schemas/execution-policy.schema.json) 校验：

| 字段 | 意义 |
| --- | --- |
| feedback_mode | per_event 或 windowed |
| max_inflight_events | 每个 actor/context 尚未取得首个真实事件回执的 output 上限；noop 也占窗口；重传不新增占用 |
| max_active_operations | 同一并发作用域内尚未确认终结的操作上限；已发出 begin/single 但未收到回执的操作也预占名额 |
| operation_scope | actor：跨该 actor 的 contexts 计数；actor_context：仅在同一 actor/context 内计数 |

per_event 必须 max_inflight_events=1：上一事件取得真实回执后才发下一事件。windowed 允许有限数量的事件在途；上限也可以配置为 1。核心不选择默认模式或固定上限。两种模式均不代表执行成功；accepted/running 只释放事件在途名额，不释放活动操作名额。

在途窗口限制“未获回执”，不是执行队列容量。提前返回 accepted 的执行器还必须遵守 limits.max_queued_updates，不能一边释放窗口一边无限积压未应用事件；容量不足须明确拒绝或施加 Profile 定义的背压，不允许静默丢掉 down/end 等操作边界。

同一 actor 可访问的 contexts 如果采用 actor 范围，必须统一采用该范围及相同的操作上限，避免通过另一个配置绕过限制。每个 actor 独立计数，user 与 assistant 不共用一个全局名额。

例如 max_active_operations=1、max_inflight_events=8：可以连续发送同一次操作的 begin/update/update/end，之后异步收到回执；不能在该操作仍活动时发送另一操作的 begin。end 已发送但尚未确认正常收尾时，活动操作名额仍未释放。

max_active_operations=2 则允许同一 actor 有两个独立操作，但依然遵守各自顺序、应用依赖和窗口上限。具体应用是否允许由 Profile 决定。这里的 8 和 2 只是样例取值，不是 Canvas 的最终性能参数。

Profile 还应定义领域依赖屏障：例如“选中对象后，取得实际选区 ID 才能调用针对选区的工具”。屏障只作用于相关动作，不阻塞声音、观察或不相关的操作。数值上限不能代替目标和依赖检查。

## 4. 回执如何释放窗口

发送方维护 event_id → 输出、所属窗口、操作的账本。一条 core.result 对应的首个真实回执，才移除该事件的窗口占用；feedback.reply_to 本身、空反馈、普通网络 ACK 和 unrelated 状态都不能释放它。后续同事件结果只更新执行进展，不重复释放名额。

环境可以在一个 feedback.updates 中放多条 core.result，逐条明确 event_id。批量反馈不是“最后一条成功，之前全部默认成功”；本草案没有隐含累计确认。某事件缺少回执时，它继续占一个名额，但 windowed 下剩余名额仍可用于符合操作和依赖约束的事件。

一个操作失败或被取消后，其已排队续接事件不得继续产生副作用，须逐条拒绝／取消并回报；缺少这些结果的在途项不能被静默删除。操作名额与事件窗口分别对账。

## 5. 就绪即反馈

有新的声音、环境事件、状态、画面、执行进展或失败时即可反馈。缺少的轨道省略或明确 empty；声音先就绪就先交付，不为凑齐画面而等待。

实现可以有界合并已经就绪的高频信息，也可以批量发送回执，但必须在协商的 receipt deadline 内交付首个事件结果，不能用慢模态作为发送条件。错误、取消和操作终态应及时报告。

全部无变化时，不制造“空反馈 → noop → 空反馈”忙循环。noop 不是心跳义务；只有模型确实输出一个无操作决策时才使用。音频不需要为了继续发送而制造 noop。

支持流式输入的模型适配器可持续接收反馈；只支持整轮输入的接口缓冲到下一次生成并标注限制，不能把网络接收冒充模型已消费。

## 6. 示例：一个操作，多个事件在途

[streaming-session.json](./examples/streaming-session.json) 使用非画布计数器的 adjust 操作：

| 时序 | 发送／交付 |
| --- | --- |
| F0 | 会话就绪；尚无视觉 |
| O1 | begin，同一 operation_id 开始连续调整 |
| O2 | update，未等待 O1 的回执 |
| O3 | end，未等待 O2 的回执；操作名额仍被占用 |
| M1 | 独立 assistant 音频，不占事件窗口 |
| F1 | user 的独立操作事实；它不是 O1/O2/O3 的回执 |
| F2 | 批量交付三个事件的结果、操作终态及新状态；画面仍可未就绪 |
| O4 | 上一操作已终结，开始工具调用 |
| F3 / F4 | 两次 reply_to=O4，分别报告 accepted 和 completed |

所有 output 都保留自己使用的 observed_feedback_seq。F2 前 O1/O2/O3 使用同一水位是合法的；F1 不会因为到达了就释放它们的窗口。相同消息去重不会重复执行或多释放名额。

另一份 [async-session.json](./examples/async-session.json) 展示音频先到、状态先到而视觉后到，以及工具的主动进展反馈。

## 7. 观察与局部同步

接收方维护每个 stream 的缓存和消费水位；模型观察可以组合不同时刻的内容，必须保留时间、来源及版本。图像声明基于某状态时必须真实匹配，状态可以晚于图像交付；没有全局模态屏障。

声音与操作仍可声明局部同步，但同步依赖必须与所选执行策略相容：不能让一个音频块等待某个尚不能发送的后续操作，而当前操作又等待该音频播放。适配器须拒绝可识别的循环依赖；串行操作可按事件边界拆分关联音频，不能以放宽发送窗口代替依赖检查。

回放按交付时刻重建各轨道当时可用内容，并保留来源时间。旧画面保持不代表重新采集；异步事件流也不代表可以抹掉中间失败或操作边界。
