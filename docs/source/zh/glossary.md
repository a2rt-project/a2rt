# 术语表

| 术语 | 含义 |
| --- | --- |
| Track | 逻辑信息分类，协议定义六种 |
| Stream | 某条轨道中的具名流，绑定来源、内容格式和时钟 |
| Event | 统一事件结构；方向决定它是执行请求还是观察事实 |
| Operation | 需要边界、并发计数和清理的操作，可跨多个事件 |
| Receipt | 执行器产生的 `core.result`，按 event_id 关联 |
| Profile | 声明领域事件、工具、状态和执行策略的环境扩展 |
| Manifest | 会话采用的能力清单，在 epoch 内冻结 |
| Epoch | 会话配置与身份绑定的一代，重建后隔离旧命令 |
| Actor | 参与者身份；与来源设备、发送方向分别表达 |
| Source | 已注册的数据或事件来源，一个 actor 可有多个 source |
| Context | 注册的环境上下文，关联 Profile 和策略 |
| Binding | 可靠传输、鉴权、资源寻址及流控的具体约定 |
| `observed_feedback_seq` | 生成 output 时实际使用的最高反馈序号，不是决策许可证 |
| `reply_to` | 反馈与 output 的关联，可多次引用同一请求 |

## 四种更新模式

- `new`：提供新的可消费数据。
- `reuse`：引用历史视觉或状态，保留原始时间；不能重放音频或事件。
- `empty`：没有新增、未就绪或不可用；不清空缓存。
- `gap`：明确的缺失范围；不等于静音。

## 容易混淆的状态

`accepted` 不表示成功；`applied` 不一定表示操作完成；`unknown` 表示实际结果尚不能确认；`cancelled` 必须以真实终止和清理为依据。

详见[轨道与时间](spec/02-tracks-and-time.md)和[执行与恢复](spec/04-execution-and-recovery.md)。
