# A2RT 协议文档

**Agent-to-Real-Time Protocol · 架构设计草案 · 2026-11-16**

A2RT 定义智能体与实时环境之间的信息承载与同步组织机制：标准根时钟提供共同刻度与容量，子时钟组织更新节拍，信息同步组组织共同窗口，自定义轨道承载角色、方向与内容。

```{note}
当前文档描述架构设计。与之匹配的新线协议版本、完整机器定义和运行时尚未发布。配置片段用于说明关系，不代表已验证的运行时实现。
```

## 从这里开始

从[协议概览](overview.md)建立概念，再按[设计接入步骤](quickstart.md)确定时钟、分组与内容契约。[配置示例](examples.md)解释窗口和容量；[草案状态](changelog.md)说明当前交付范围。

## 四层组织关系

<img src="{{ base }}assets/clock-groups.svg" alt="根时钟、子时钟、同步组与轨道">

共同的时钟不自动产生共同等待。每个接收端按选定 Profile 判断自己的窗口是否可交付，其他同步组独立推进。Core 保留身份、时间与通用状态；播放、恢复、完整性和内容校验由 Profile 定义。

| 阅读目标 | 文档 |
| --- | --- |
| 理解节拍、容量与每轨单帧 | [时钟、同步组与轨道](spec/01-clock-sync-group-track-model.md) |
| 协商媒体及 JSON 内容契约 | [媒体类型与格式协商](spec/02-media-types-and-negotiation.md) |
| 划分通用机制与领域实现 | [Core 与 Profile 职责](spec/03-core-profile-responsibilities.md) |
| 区分系统通知和输出、任务、会话边界 | [system 与生命周期](spec/04-system-track-and-lifecycle.md) |
| 查看画布场景的具体选择 | [Canvas 适配要求](profiles/canvas.md) |

```{toctree}
:caption: 开始了解
:maxdepth: 1
:hidden:

overview
quickstart
```

```{toctree}
:caption: 核心规范
:maxdepth: 1
:hidden:

spec/01-clock-sync-group-track-model
spec/02-media-types-and-negotiation
spec/03-core-profile-responsibilities
spec/04-system-track-and-lifecycle
```

```{toctree}
:caption: 应用 Profile
:maxdepth: 1
:hidden:

profiles/canvas
```

```{toctree}
:caption: 参考资料
:maxdepth: 1
:hidden:

examples
glossary
changelog
```
