# 示例与校验

示例采用独立的计数器环境，不依赖画布实现。所有 JSON 和校验器都在仓库的 `protocol/` 下。

## 可下载文件

| 文件 | 内容 |
| --- | --- |
| [session.json]({{ base }}protocol/examples/session.json) | 清单、时钟、来源、stream 和 Profile 引用 |
| [counter.profile.json]({{ base }}protocol/examples/counter.profile.json) | 计数器事件、工具、状态和策略 |
| [streaming-session.json]({{ base }}protocol/examples/streaming-session.json) | 连续操作、多事件在途、独立音频、批量回执 |
| [async-session.json]({{ base }}protocol/examples/async-session.json) | 模态先后到达、工具进展、历史引用和控制查询 |
| [message.schema.json]({{ base }}protocol/schemas/message.schema.json) | 四种消息和 TrackUpdate 的 JSON Schema |
| [event.schema.json]({{ base }}protocol/schemas/event.schema.json) | Event 的核心结构 |
| [manifest.schema.json]({{ base }}protocol/schemas/manifest.schema.json) | 会话能力清单 |
| [execution-policy.schema.json]({{ base }}protocol/schemas/execution-policy.schema.json) | Profile 执行策略 |

## 读懂流式示例

| 顺序 | 发生什么 |
| --- | --- |
| F0 | 发布初始反馈，视觉尚未就绪 |
| O1 / O2 / O3 | 同一操作的 begin、update、end 连续发出 |
| M1 | assistant 独立发送音频，不占事件窗口 |
| F1 | 用户的已发生事件，不是 O1～O3 的回执 |
| F2 | 批量交付三个事件的结果与操作终态 |
| O4 | 开始新的工具操作 |
| F3 / F4 | 同一请求先得到 accepted，之后得到 completed |

媒体资源采用 `example:` 占位引用，没有可播放的音频或可解码的图像。示例里的采样率和时间间隔只用于说明，不是协议统一要求。

## 校验范围与限制

```sh
python protocol/validate_examples.py
```

正例覆盖多事件在途、批量回执、重复关联进展、另一 Profile 的并发操作、视觉先于状态等。反例覆盖窗口溢出、回执关联错误、end 后续接及每事件策略下提前发送等。

校验器没有实际驱动媒体播放、网络超时或输入清理，也不是全协议一致性测试。实际资源就绪、时钟漂移、跨服务去重与恢复必须另行验收。
