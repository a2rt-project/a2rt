# A2RT 协议文档

**Agent-to-Real-Time Protocol · 0.2 草案**

A2RT 定义智能体与实时环境之间的事件、媒体、观察和执行反馈。各轨道独立更新，已就绪的信息立即交付，同时保留来源、时间与因果关系。

```{note}
当前交付为协议规范、JSON Schema、可校验示例和文档校验器。尚未提供生产 SDK、完整传输绑定或硬实时截止保证。
```

## 从这里开始

第一次接触 A2RT，先读[协议概览](overview.md)和[快速入门](quickstart.md)。准备实现适配器时，再按顺序阅读核心规范。想直接看消息，打开[示例与校验](examples.md)。

## 一个持续运行的闭环

环境持续采集声音、画面和状态；智能体按 Profile 的策略发送事件；执行器报告真实进展。声音不必等待操作，回执不必等待画面，局部依赖仍须被明确满足。

| 你想了解 | 从哪里读起 |
| --- | --- |
| 协议解决什么问题 | [协议概览](overview.md) |
| 如何定义环境能力 | [核心与 Profile](spec/01-core-and-profiles.md) |
| 如何表达不同步的音频和画面 | [轨道与时间](spec/02-tracks-and-time.md) |
| 什么时候可以发送下一条事件 | [异步反馈与执行策略](spec/03-feedback-loop.md) |
| 取消、超时、重连如何对账 | [执行与恢复](spec/04-execution-and-recovery.md) |
| 消息字段和 Schema 在哪里 | [消息与校验](spec/05-wire-and-validation.md) |

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

spec/01-core-and-profiles
spec/02-tracks-and-time
spec/03-feedback-loop
spec/04-execution-and-recovery
spec/05-wire-and-validation
```

```{toctree}
:caption: 参考资料
:maxdepth: 1
:hidden:

examples
glossary
changelog
```
