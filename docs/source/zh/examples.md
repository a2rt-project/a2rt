# 配置示例与设计检查

当前示例来自[规范第 01 章](spec/01-clock-sync-group-track-model.md)，用于说明架构，不是新线协议的生产消息。下载[完整配置 JSON]({{ base }}assets/architecture-example.json)。示例中的 `example:` 引用是占位符，实际接入需提供 Profile 的真实内容契约。

## 从根时钟计算窗口

示例 root 为 1,000 Hz，标准单位 1,024 字节，每根刻度容量为 1 个单位。交互子时钟的父周期为 100，所以交互组窗口长 100 ms。`start_tick=0` 且无偏移时，前三窗为 `[0,100)`、`[100,200)`、`[200,300)` ms。

若子时钟偏移 3 根刻度，窗口改为 `[3,103)`、`[103,203)`、`[203,303)` ms。起点无需重合，但窗口边界必须精确落在整数根刻度。

## 共享预算，不重复分配

| 组 | 周期 | 每窗上限 | 每 100 ms 的上限 |
| --- | --- | --- | --- |
| interaction | 100 根刻度 | 64 标准单位 | 64 |
| tactile | 10 根刻度 | 2 标准单位 | 20 |
| system_control | 10 根刻度 | 1 标准单位 | 10 |

三组共 `64 + 10 × 2 + 10 × 1 = 94` 个单位，根预算为 100。这个总量算式只展示共享关系；实际突发、封装开销与交付期限仍需 Binding 和运行时验证。

## 区分内容上限与组容量

媒体格式可声明图片不超过 1,000,000 字节，但 interaction 的 64 个 1,024 字节单位不能容纳一张接近 1 MB 的图片。格式约束与组预算须同时满足，不能以拆片规避任一上限。

## 每轨单帧的位置

`(epoch, sync_group_id, frame_seq, track_id)` 定位一个轨道数据帧。不同轨道可各有一帧；双向状态轨道的双方共享一个位置。原帧重传或分片仍属于原位置，不重复交付；不同内容或来源冲突不能覆盖原帧。

## 本仓库的检查范围

```sh
python scripts/check_protocol_docs.py
python scripts/build.py --preview
python scripts/check_site.py
npm test --prefix worker
```

这些命令检查文档来源、配置示意的结构与算式、双语网站链接，以及当前 AI 索引与检索行为。它们不执行 Canvas 本地 mock，也不证明通用运行时合规。运行时的一致性、内容处理和时延目标仍需独立验证。

## 当前 Canvas Realtime 配置

[Canvas Realtime](profiles/canvas-realtime/index.md) 提供可检查的 [Profile]({{ base }}protocol/profiles/canvas-realtime/profile.json) 和 [会话配置]({{ base }}protocol/profiles/canvas-realtime/session.json)。该实例为 1,000Hz 根时钟、10Hz 交互与 100Hz 独立通知，共七条协议轨道；不要与上面的通用配置示意混用。

它使用真实 24kHz 单声道 L16 字节：100ms 对应 2,400 个样本、4,800 字节。观察由发送端准备，接入层验收；超时由运行时在下一个合法周期重新采集。详见[交互契约](profiles/canvas-realtime/interaction.md)和[二进制 Binding](profiles/canvas-realtime/binary-binding.md)。这些是本地 Profile 选择，不代表 Core 强制的错误通知或恢复流程。
