# Canvas Profile：A2RT 0.2 的画布实现

Profile ID：`canvas.excalidraw`；Profile 版本：`0.1`（首次 A2RT 版）；核心线协议：`a2rt/0.2`。日期：2026-11-15。

本 Profile 将画布事件、选区、对象及原生操作辅助绑定到 [A2RT](../../README.md)。机器定义见 [profile.json](./profile.json)；可运行实现见 [六轨验证网页](../../../../../benchmarks/canvas_event_loop/README.md)。旧 `naoix.canvas-loop.v2` 文档作为历史版本保留。

当前实现是受限 mock：双方行为、异步调度和执行结果由脚本产生，画面由 Excalidraw 0.18.1 原生渲染。没有接入真实模型、真实 MCP 服务或生产协作后端。

## 1. 每个 actor 同时一个 task

这里 task 即 A2RT 的 `operation`，不是一条消息、一段声音或一帧画面。会话选择并冻结 `single_task_streaming`：

```json
{
  "feedback_mode": "windowed",
  "max_inflight_events": 8,
  "max_active_operations": 1,
  "operation_scope": "actor"
}
```

- `assistant` 和 `user` 各有一个任务名额，可以同时操作。限制按 actor 生效，不是整张画布只能有一个任务。
- 一次拖动从 down 到 up/cancel 占用一个名额，其中多个 move 可以连续发送，不需要逐条等待反馈。窗口 8 只限制尚无回执的事件数，是当前 mock 的冻结配置；调整窗口须重新协商并更新清单哈希。
- 同一 actor 拖动期间不能插入工具调用；工具执行中也不能插入另一拖动。冲突请求返回 `OPERATION_CONFLICT`，原任务继续。
- `assistant` 收到任务真实终态才启动下一任务。仅发出 up、收到中间事件的 applied 或收到一个新画面，都不等于任务完成。
- `user` 在本地执行，任务本地完成即可继续下一任务，随后异步上报已经发生的事件及结果。无需等待网络、更无需等待 AI 批准。快捷键触发的新任务也必须遵守本地边界；组合键作为当前任务的输入状态不另开任务。
- 声音、画面、状态、`core.noop`、查询控制不占任务名额。讲话和拖动可以同时发生。

对于异步工具，名额在开始执行时预留，成功、失败或取消后释放。选区过期导致失败也必须释放预留名额。超时是“未确认”，不能直接认定任务结束。

本 Profile 不加对象锁。生产适配仍采用 Excalidraw 元素协调的方向；本 mock 仅验证不同 actor 的任务调度，没有实现生产级同对象冲突协调、多人合并或失效捕获取消。

## 2. 双向统一事件

双方都使用 A2RT Event：`event_id / actor_id / context_id / time / operation_id / phase / type / payload / timing`。模型请求放在 `output.event`，用户已发生事件放在 `environment.events` 的 `core.event_record`，其 `disposition` 为 `observed`。后者不得重复执行。

当前能力边界：

| 类型 | 含义 | 操作边界 |
| --- | --- | --- |
| `canvas.pointer` | 逐点鼠标状态事件；scene 坐标、单鼠标指针、左键 | down/begin → move/update → up/end 或 cancel/cancel |
| `canvas.pointer` | 无按键的悬停移动 | move/single；单条完成，也受 actor 名额限制 |
| `core.tool_call` | 按 MCP 工具调用形状提交 `server_id/name/arguments` | begin；执行器异步回报任务终态 |
| `core.noop` | 本次无操作 | operation_id=null，phase=none；不释放现有任务 |

`canvas.pointer` 不包含 duration、终点计划或服务端插值计划。一次曲线是多个真实事件：

```json
{
  "event_id": "e_move_2",
  "actor_id": "assistant",
  "context_id": "board_1",
  "time": {"clock_id": "demo_clock", "t_us": 4260000},
  "operation_id": "move_rect",
  "phase": "update",
  "type": "canvas.pointer",
  "payload": {
    "name": "pointermove", "pointer_id": 1, "pointer_type": "mouse",
    "space": "scene", "x": 202, "y": 204, "button": -1, "buttons": 1
  },
  "timing": {"mode": "immediate"}
}
```

必须同时校验 phase 与鼠标状态：down=begin/button0/buttons1；按住移动=update/button-1/buttons1；up=end/button0/buttons0；cancel=cancel/button-1/buttons0；悬停=single/button-1/buttons0。

执行器按 actor 保持事件顺序并对 event_id 去重；同 ID 内容改变拒绝。operation_id 绑定 actor/context/type，不可跨类型复用，终结后不可重新打开；迟到 move 不得继续改变画布。

正常 end 和 cancel 都清除 buttons、capture、临时框选/擦除预览及活动任务。cancel 不是 undo：保留已发生位移和绘制；尚未提交的擦除候选不删除。当前有效选区可以保留。`noop` 不承担取消语义。

## 3. 工具与选区

工具能力与 inputSchema 一起写入冻结 Profile，并由会话清单记录内容 SHA-256。模型不能调用未协商的任意名称。这里的 `naoix-editor` 是当前实现的本地适配器 ID，不是 A2RT 核心命名，也不是官方 Excalidraw MCP 服务。

| 工具 | 分类与参数 | 前置条件 |
| --- | --- | --- |
| `editor_set_tool` | 画笔上下文；selection / ellipse / freedraw / eraser | 无需选区；当前 actor 无其他活动任务 |
| `editor_set_style` | 默认画笔或选中元素；scope 明确为 defaults / selection / defaults_and_selection | defaults 无需选区；selection 必须非空；defaults_and_selection 允许空选区，仅更新默认值 |
| `editor_action` | 多元素调整；当前实现 alignTop / group | 至少两个有效选中元素；group 不允许重复分组 |

工具参数保持工具原始形状，例如：

```json
{"server_id":"naoix-editor","name":"editor_action","arguments":{"action":"group"}}
```

模型可先点击或框选，再从反馈获得真实元素 ID、组 ID，并进行后续工具调用。当前工具子集绑定当前选区，不要求模型再次填写 ID；以后接入需要显式 ID 的 MCP 工具时，可直接使用反馈中的 ID，另行声明其 inputSchema 和 target binding。

`assistant` 的选区型调用以 `observed_feedback_seq` 之前最新收到的 `canvas.state` 为依据。环境维护该观察水位对应的选区；执行时核对 actor、selection revision、成员和 ready 状态，不一致返回 `CONTEXT_STALE`，不暗中使用新的目标。调用者收到新选区后以新 event_id/operation_id 重新决策，不盲目重发旧操作。

这个子集没有声明缩放、旋转、图片导入、键盘、多指触控、撤销或完整 MCP 能力。原生选中框、锚点可见不代表 mock 已实现所有锚点拖动。生产适配接入实际能力后再扩充 Profile 与测试。

## 4. 领域状态、结果与画面

`environment.state` 包含三个 stream：

- `canvas_state` / `canvas.state`：双方工具、样式、指针、选择、对象、组、视口和任务状态。
- `receipts` / `core.result`：按 event_id 关联真实执行结果，可异步批量送达。
- `control_results` / `core.control_result`：查询、取消等控制请求的结果，独立于操作窗口。

每位参与者的 selection 包含 `revision/status/element_ids/group_ids/editing_group_id/bounds`；参与者另有 `active_operation_id`。objects 保留元素 ID、version、删除状态与几何数据；groups 返回组 ID 和成员。删除元素不能继续出现在有效选区中。

版本分别解释：

| 字段 | 含义 |
| --- | --- |
| state 的 revision（rN）、value.snapshot_seq | 完整状态快照版本；光标或任务状态变化也可产生新版本 |
| board_revision、元素 version | 画布内容变更版本，不等于画面帧数 |
| selection.revision | 某 actor 的选区变化 |
| visual 的 stream seq / view_N | 独立画面更新及采集标识 |
| core.result.revision | 同一事件回执的进展版本 |

指针中间事件返回 `status=applied, operation_status=active`，只释放该事件的在途名额。up 返回 completed/completed，cancel 返回 cancelled/cancelled，才释放任务名额。工具可先返回 running/active，再返回 completed/completed。失败返回 error 和终态；对第二任务的拒绝不改变原任务。查询恢复原有回执时沿用原 revision 和内容，不重新执行。

画面和状态分别更新。画面携带采集时间与 `source_state_refs`，历史画面保留原版本，不能把较新的 JSON 标成旧图的来源。迟到旧图可以进入日志，但实时呈现不回退覆盖较新的采集。倒退回放可以显式恢复历史观察。

mock 视觉资源为协商的 `application/vnd.a2rt.canvas-snapshot+json`：`mock:canvas-view/view_N` 引用不可变快照，网页通过原生 Excalidraw 渲染。它不是已经传输并解码的 PNG/视频性能测试。生产发送图片或视频时必须在实际采集后绑定来源版本，不能混用这个 mock 资源类型。

光标样式保持一致，显示名为 `user`、`assistant`；工具语义由 JSON 表达。选中框、锚点、框选区域和协作者光标均来自原生渲染；mock 擦除候选用降低透明度表示，松开后提交删除。

## 5. 六轨独立调度与恢复

网页仍展示六条逻辑轨道：assistant.audio、assistant.events、environment.audio、environment.events、environment.visual、environment.state。共八个具名 stream；逻辑轨道数不等于连接数或时钟数。

没有固定的“一帧输出配一帧反馈”。同一次拖动的事件可先后发出，回执随后批量到达。环境只发布已就绪轨道，音频和状态不等画面。某条轨道未更新表示本条消息无新增数据；首次画面未就绪用 empty/not_ready；保留旧画面不伪造新采集。

当前 mock 的注入参数，仅用于复现时序，不是实测延迟或标准值：

| 项目 | 配置 |
| --- | --- |
| 指针事件间隔 | 60 或 80 ms；事件边界保留 |
| assistant → 环境 | 30 ms |
| 状态准备 / 反馈传输 | 25 ms / 20 ms |
| 工具执行 | 120 ms，期间占该 actor 名额 |
| 回执批次 | 每 120 ms 一个边界，仅有回执时发送 |
| 画面采集 | 160 ms；准备通常 65 ms，故障章节 650 ms |
| 音频 | assistant 每 100 ms、user 每 80 ms；24 kHz 单声道 PCM |
| 播放 | 公共演示时钟；资源就绪后在源时间 +140 ms 播放 |
| 回执超时 | 600 ms 后走独立 query；演示 80 ms 处理 +20 ms 反馈恢复 |

两段预录音频按 start_sample/sample_count 截取，与网络往返时长无关。当前事件为 immediate，不声明音频采样级执行依赖：页面展示“讲话与操作同时进行”，不声称已验证真实模型的精确语义同步。

窗口满时暂停发送新操作事件，保留原顺序；音频、用户本地操作、视觉、状态和控制继续。演示通过 query 取回真实回执释放窗口，避免重复执行副作用。查询响应本身不代表原操作完成，必须看关联的 core.result。

生产实现继续遵守 A2RT 的有界恢复：查询/重同步超过协商次数或截止时间后进入明确 suspended/unknown，不永久隐藏等待、不擅自释放任务、不把历史画面当成功回执；取消要等执行器真实清理确认。断线时还需执行器 idle watchdog 清理按键和捕获。网页目前实现正常路径、回执延迟后成功查询路径和显式 pointercancel；持续断线、watchdog、丢失末尾事件、跨服务重连及失败查询状态机仍属后续真实执行器工作。

实时结果不等待数据库或录像。快照中的 persisted_revision 仅是继承的 mock 元数据，网页没有持久化实现，不以其变化判定任务完成。

## 6. 验证方式

网页提供“正常异步”和“延迟与恢复”两个场景。可按消息或画面步进、任意拖动时间、播放双方音频、看原始消息/选区/观察快照、导出整场 JSON。

观察快照只来自已交付消息；调度器在途数、发送队列和 user 本地状态单独标为诊断。画布底部显示实际绘制画面的版本与当前状态版本；浏览器渲染晚于选中消息时保留旧图并显示“正在呈现”，不假装已经完成渲染。

自动检查覆盖结构、选区引用、每 actor 的名额、在途窗口、异步回执、不可变画面来源、迟到帧处理、终态清理、去重、选区过期、音频采样范围和清单哈希。验证命令见网页 README。
