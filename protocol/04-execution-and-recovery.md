# 执行、恢复与传输边界

## 1. 操作状态机

活动操作数按所选 Profile 的 max_active_operations 和 operation_scope 计数，不由 Core 固定为 1。begin/single 发出即预占名额，真实终态才释放；事件在途窗口另行计数。下表描述单个操作的规则，不能据此限制其他合法并发操作。

| 当前状态 | 允许 |
| --- | --- |
| 尚未开始 | 有操作名额及事件窗口时发送 begin 或 single |
| 连续操作 active | 同 operation_id 的 update/end/cancel；按策略允许提前发送，执行器按序应用 |
| 工具 running | 等待真实工具结果；不能给该工具 operation 插入指针 update；可走控制通道取消 |
| end/cancel 已发送、清理中 | 不再发送该操作的普通续接；名额保持，直到确认清理完成 |
| 结果 unknown | 查询、取消、恢复；暂停该操作续接及与未知副作用冲突的动作 |

Profile 负责开始、结束、取消的具体动作。指针的正常 up 应先完成编辑器收尾再释放按键／捕获；取消也要释放，但保留已经协调后的有效内容与上下文。A2RT 不把每条反馈的结束当作 operation 结束。

## 2. 执行结果轨

core.result 在 environment.state 的独立 stream 中发送，包含：event_id、operation_id、revision、status、operation_status、time、result、error。revision 对同一个 event_id 单调递增；重复版本内容必须相同。

| status | 含义 |
| --- | --- |
| accepted | 已校验、登记去重并接纳；尚未确认应用 |
| running | 执行仍在推进 |
| applied | 该事件实际应用；连续操作可能仍 active |
| completed | 该事件完成；若是操作终结事件，还必须确认清理完成 |
| rejected | 执行前拒绝，不产生该请求的领域副作用 |
| failed | 执行失败，可能已有部分副作用 |
| cancelled | 已确认终止与所需清理；不能仅因发出取消请求就填写 |
| unknown | 暂时不能确认实际结果，保留账本和对账路径 |

operation_status 为 active/completed/failed/cancelled/unknown；noop 为 null，不改变已有操作。拒绝插入的新操作不能结束正在运行的旧操作。result 的领域部分按能力声明校验；error 带稳定 code 和说明。

time 是该状态获知或发生的实际执行器时间；Profile 可在 result 中提供开始、首次应用、完成等更细时间，并注明时钟。遥远工具返回成功而本地环境尚未核实效果时，保留 running；不能提前报告本地 completed。

已确认终态不可重新变成 active；unknown 可以在对账后收敛为真实结果。不同事件的 receipt 更新可以与新的 output 并行交付，不制造额外操作。

## 3. 去重与重传

message_id 用于消息去重，event_id 用于实际动作去重，媒体使用 stream_id 和采样范围去重。收到同 ID 同内容返回已有事实，不重复执行、播放或交付模型；同 ID 不同内容必须拒绝。

执行器须在可能产生副作用前原子登记请求及状态。在进程崩溃后无法证明是否执行的事件必须标记 unknown，不能靠一个丢失的内存 Map 宣称 exactly-once。跨服务副作用还依赖执行端的去重键、持久账本或对账能力；MCP 请求 ID 本身不能提供此保证。

事件回执丢失时，可重传相同消息以查询已登记结果；适配器无法保证该重传不再次派发远程写入时，应走 query 控制路径，禁止盲重发。没有“首个 feedback 才授予下一轮”的全局门禁。

## 4. 超时与恢复

- feedback_deadline_ms：每个 output 等待首条 core.result 的期限；不是等待任意反馈，更不是等待视觉。
- operation_idle_timeout：连续操作停滞；与合法的慢工具总运行时间分开。
- media_dependency_timeout：等待显式关联媒体／事件，仅影响该同步关系。
- resource_timeout：媒体资源不可用，反馈该轨道 empty/unavailable 或 gap，其他轨道继续。

全部为协商参数，不规定一个适用于所有环境的固定毫秒数。

未超时但缺少某条回执时，windowed 策略可以使用剩余窗口发送合法事件；per_event 策略则等待。窗口满了只暂停该 actor/context 的普通 output，不暂停媒体、观察和 control。

达到回执期限后，本地协调器记录 timeout/unknown，不伪造环境反馈或释放名额。该 actor/context 的普通 output 暂停并通过独立 control 查询／恢复；若该操作的资源影响其他 context，Profile 还须暂停相应冲突动作。查询受 limits.recovery_max_attempts 和 recovery_deadline_ms 双重上限限制，到任一上限仍不能确认则进入明确的 suspended 状态，向调用方展示原因，不能无限忙等。

查询确认事实后，环境须补发对应 event_id 的 core.result，发送方据此释放在途名额并重新检查操作状态、依赖和目标是否有效；core.control_result 的 completed 本身不等于事件成功。原本未执行的请求可以返回 rejected；已经执行则返回真实结果。仍为 unknown 时不得继续冲突动作。完整对账或新 epoch 恢复完成前不自动重放旧命令；迟到回执只补账，不直接触发旧动作再次执行。

control 的 action 为 cancel/query/resync，携带 request_id 和目标 operation_id 或 event_id。cancel/query 必须有至少一个目标，resync 可以 target=null。响应通过 environment.state 中的 core.control_result 发送，字段为 request_id、revision、status（accepted/completed/failed/unknown）、result、error；同请求 revision 单调递增，重发保留 ID，控制结果不隐含释放事件窗口或操作名额。

取消的送达 ACK 不等于清理成功。cancel 的 completed 要确认所需清理；目标原事件的状态另用 core.result 更新，不能只关闭控制请求而伪造目标已经停止。query 的 completed 表示查询已完成，查询结果可以仍为 unknown。control 不在普通工具／指针任务中排队，避免卡死时无法释放。环境端至少须能接收这三类控制并回报明确结果。

环境也可以自主停止会话或取消活动输入，通过主动反馈告知真实状态，不等待 assistant 发 control。模型生成中断由绑定层通知模型协调器；A2RT 的旧 epoch 隔离继续生效，不因为模型尚未停止生成就接纳旧命令。

重连后先核对操作与媒体位置，再创建新 epoch、清单和 F0。隔离旧输入，清理捕获和未播放的关联声音；保留有效环境事实。epoch 变化不会自动停止已经派发的外部调用，必须等待其对账／隔离完成后才执行冲突的新写入。

## 5. 背压和缺口

流控按 stream 和数据类型执行，不以“最慢轨道决定整个会话速度”为原则。

- 回执、操作边界和取消不可静默丢弃；无法可靠交付时暂停相关新副作用并进入恢复。
- 视觉可以在发布前合并待渲染版本；未发布中间图不算虚构的新图。已发布记录不可修改。
- 状态完整快照可以合并，但不能因此吞掉操作结果或覆盖缺口说明；依赖增量的扩展必须保持可还原性。
- 音频不能静默跳样或用旧音频填充。超出缓冲能力时报告明确 gap、降级或终止该流。
- 环境事件可批量交付并保留顺序；丢失映射时发出 Profile 定义的 coverage gap，并提供实际状态。不得依据状态变化伪造精确输入过程。

晚到数据保存为历史证据时，不让较旧状态覆盖已确认更新的实时状态。原始记录与“当前可用视图”分别管理。

## 6. 绑定与安全

v0.2 假设逻辑消息可按发送方有序、可靠地交付；跨独立媒体通道使用显式资源引用与就绪判断。WebSocket、HTTP 双向流或其他传输的具体握手、错误码和包格式需要单独绑定文档，本草案不把任意 WebSocket 服务视为兼容实现。

部署必须鉴权、限制来源与工具权限，并保护传输。媒体引用由受信任绑定解析，限制来源、大小、内容类型和生命周期；不直接抓取模型任意指定的 URL。外部环境文本是数据，不能改变已协商协议、授权或工具清单。

六条逻辑轨道与模型 API 的角色映射独立。任何基于 RTP/RTCP 或其他媒体协议的同步都仍需映射 A2RT 的 stream、时钟、事件和状态版本，媒体时间同步不能替代操作回执。

## 7. 录像

录制初始状态、清单及哈希、事件、实际结果、轨道更新、媒体资源、时钟映射和消费水位；记录采集／应用时间和交付顺序。保存异步进行，保存进度作为独立状态 stream，不能阻塞现场。

回放不得把历史事件再次发往实时执行器。跳转恢复各轨道的历史缓存、状态和媒体游标；视觉保持上一张图时显示其真实时间与版本，不伪装成每一帧均重新采集。
