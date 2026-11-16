# 二进制音频 Binding 与真实传输

Binding 标识为 `canvas.a2rt.mock.v2`，Profile 版本 `0.3.0-draft`，会话通过 `profile_version` 确认版本。这是本 Canvas 实例的传输绑定，不为 A2RT Core 声明新线协议版本。音频轨道的数据帧承载真实 PCM 字节；本次时钟和恢复职责调整不改变二进制封装。

## 1. 格式与载荷

音频轨道的格式配置如下，assistant.audio 和 user.audio 都引用它：

```json
{
  "format_id": "audio",
  "media_type": "audio/L16",
  "constraints": {"rate": 24000, "channels": 1, "max_encoded_bytes": 131072}
}
```

L16 使用有符号 16 位、二进制补码、大端字节序；24,000Hz 是允许的采样率。参见 [RFC 2586 §3–4](https://www.rfc-editor.org/rfc/rfc2586.html#section-3)。实际载荷无 WAV 文件头、URL、Base64 或 JSON 数值数组。WAV 仅作为服务端模拟麦克风与模型语音源，按 RIFF 块读取、校验格式，再转换为 L16。

每 100ms 为 2,400 个样本，即 4,800 字节；180ms 为 8,640 字节。零样本空帧的二进制载荷长度为 0；已知静音使用真实的全零 PCM 样本。未知缺失不能补成静音。

音频时间描述放在数据帧头的 `audio` 字段中，格式内容限制仍由 media_type/constraints 决定。该字段是 Binding 元数据，不是把音频重新声明为 JSON 媒体，也不是第二条音频轨道。

```json
{
  "track_id": "assistant.audio",
  "source_id": "model",
  "audio": {
    "mode": "data",
    "start_sample": 24000,
    "sample_count": 2400,
    "coverage": {"clock_id": "root", "start_root_tick": 1100, "end_root_tick": 1200},
    "requires_events": ["ev_assistant_010"]
  },
  "body": {"offset": 0, "length": 4800}
}
```

`body` 指向同一包二进制区中的字节。采样率和声道来自协商格式；`audio` 不重复保存可覆盖它们的配置。[audio-metadata.schema.json](./schemas/audio-metadata.schema.json) 只约束这个帧头，不能代替实际 PCM 长度和采样校验。

其他格式继续为 application/json：event、visual、state、system，使用各自的 constraints.schema_ref。visual 仍是原生 Excalidraw 场景快照，未声称改成视频编码。

## 2. 包结构

`A2B2` 包定义如下；所有整数为无符号大端：

| 部分 | 长度 | 内容 |
| --- | --- | --- |
| magic | 4 字节 | ASCII `A2B2` |
| header_length | 4 字节 | UTF-8 JSON 帧头的字节长度 |
| header | header_length | 会话、epoch、packet_id、发送刻度、同步组、frame_seq、root_window、data_frames |
| binary bodies | 变长 | 按帧头顺序紧密排列的原始 L16 字节 |

JSON 轨道的数据帧在帧头中使用 `payload`；音频轨道使用 `audio + body`，不能再同时包含 JSON payload。二进制区的 offset 从 0 起连续排列，不允许重叠、空洞、越界或未声明的尾随字节。包大小上限为 1MiB，仍须服从更严格的帧／组／根容量。

完整帧头由 [packet.schema.json](./schemas/packet.schema.json) 定义。浏览器解码后，音频 payload 是 Uint8Array；网页将其显示成字节数与十六进制预览，明确标识为“二进制摘要”。这个 JSON 检查视图不是传输中的 PCM 编码。

每条轨道每周期仍只有一个数据帧。不同包可贡献不同成员，相同原帧可以去重；同位置不同元数据、发布来源或任一 PCM 字节不同均拒绝。容量校验包含 4 字节流记录长度、8 字节包前缀、UTF-8 帧头以及实际音频体，不能只统计 JSON 描述大小。

## 3. HTTP 流绑定与回放

本次以真实本地 HTTP 流验证发送和接收，不将进程内对象引用当作传输：

1. `/api/session?mode=normal|faults|suspended` 提供会话配置和回放索引，包含文字、图形、样本范围及字节摘要，但不提供任何音频样本或 WAV 地址。
2. `/api/stream?mode=...` 返回 application/octet-stream。流中每个单元是 `uint32 packet_length + A2B2 packet`，服务端按记录中的根刻度以 1× 节拍逐包发送，遵守 HTTP 写入背压；客户端关闭连接会取消待发送定时任务。
3. 接收器从 ReadableStream 增量读取。HTTP chunk 可以切在长度、帧头或任意样本字节中，也可以合并多个包；重组完成后交给共享的 ModelIngress，按帧校验并逐窗触发完整观察回调。迟到、重复、过期和暂停后的不完整观察不会进入模型。传输分块不是新的轨道数据帧。
4. 收齐并验证后，原生 Web Audio 从收到的 L16 字节构造 AudioBuffer。浏览器没有 WAV URL 获取或预置音频播放的备用路径。首轮约 24 秒接收完成后，才开放播放、拖动和逐帧检查；再次查看已接收场景使用接收缓存。

这是“按实时节拍传送并录制，再回放检查”的验证网页，不是未实现却标称在线的真实模型会话。预生成动作和场景来自 mock，媒体字节经过真实 HTTP。模拟音画等待与网络实际读取耗时分别记录；这些测试不证明公网吞吐或模型推理延迟。

等待整段接收完成是本网页支持录制检查与任意拖动的选择，不是 A2RT 模型输入的要求。接收器已支持 `onObservation` 逐窗回调，由实际收到的字节组成观察，通过完整性检查后触发；回放索引不能授予不完整窗口交付资格。包头解析、分片重组、PCM 长度检查及去重属于 Binding／接入层；网页显示的十六进制摘要和传输诊断不是模型的输入格式。真正的模型媒体适配仍需按模型接口接入。

按“谁发送谁负责”，服务端在发送前准备并校验载荷，接收器承担验收与传输重组；发现截断或不符时报告失败，不自行修补媒体内容。重新发送或重新采集属于发送侧恢复，具体策略由 Profile 定义。此 HTTP Binding 验证固定 mock 的逐包传输与接收，未实现生产环境的双端重连／补传控制通道；不能把接收器报错等同于恢复已经完成。

这里的失败报告是当前接收器抛出的本地错误，由调用方／网页处理；没有向发送端回送通用错误控制消息的接口。演示中的 system 超时通知由 mock 协调器按 Canvas 契约产生，不能把它当作真实 HTTP 接收错误已触发远端恢复的证明。A2RT Core 不强制错误控制消息或额外通道；未来若需要跨端通知，由 Profile 选择自定义轨道、另建通知通道或其他方式，再由 Binding 实现。

图形任务与音频播放遵守本实例的演示时序。user 音频在 assistant 因画面故障暂停时仍继续采集和传输；它可进入独立的接收收集器，但不伪造完整视觉反馈。恢复时重复覆盖的历史样本须逐字节一致；播放去重后只消费一次。客户端检验所有待播放区间已收齐，遇到缺口、中断或冲突直接报错，不静默换成整段原文件播放。

## 4. 预算、缓存和导出

标准帧单位仍为 1,024 字节，业务组每信息帧 256 单位，system 组 4 单位；根每周期 256 单位。A2RT 单位计量 A2B2 全包及 4 字节记录长度前缀，不含 HTTP 传输层；网页 wire_bytes 记录读到的整个流，同样包含长度前缀。这是本地验证配置，不是网络部署推荐。

模型／环境待交付队列限制保持不变；HTTP 写缓冲执行背压。二进制解析器拒绝超长包、截断、非法 offset；PCM 解码器要求样本数×声道数×2 与字节数相等。录制缓存与待交付队列分开，当前会话 PCM 上限为每 actor 60 秒。回放音频与反馈音频使用相同收到的字节，没有第二套音频源。

导出 `.a2rt` 文件保留真实二进制数据：`A2R2 + uint32 index_length + JSON index + 多个 length-prefixed A2B2 包`。导出单元包含对应输出、反馈原包和其引用的用户事件；导出会话包含所有原包。JSON index 保存 manifest、传输统计和音频字幕信息，不把样本改成 Base64。

## 5. 校验职责

JSON Schema 校验全部帧头及非音频载荷；音频内容通过实际字节长度、RIFF 源格式、端序、时间覆盖、逐样本对照、重复区间一致性和接收重组测试验证。测试包含真实 1× HTTP 传输和故障场景接收，不只检查元数据字段。
