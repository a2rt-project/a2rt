# A2RT — Agent-to-Real-Time Protocol

A2RT 是面向智能体与环境的实时业务信息交互协议，提供可配置的多轨信息通道和统一时间契约。标准根时钟提供共同刻度与容量，子时钟组织节拍，信息同步组组织窗口，自定义轨道承载角色、方向与内容格式。

**当前状态：2026-11-16 架构设计草案。** Canvas Realtime 已有 0.3.0-draft Profile、会话配置、Schema 和本地 mock 的实现说明；覆盖全部当前约束的通用线协议版本与运行时尚未发布。配置示例用于说明设计；文档检查不代表运行时一致性验证。

[官网](https://www.a2rt.org/) · [Docs](https://www.a2rt.org/docs/)

## 本地预览

需要 Python 3.11+；Worker 检查需要 Node.js 22+。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_protocol_docs.py
python scripts/build.py --preview
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:4173/`。`--preview` 使用当前双语索引进行本地全文搜索，不连接生产 AI Worker。正式构建使用 `python scripts/build.py`，AI 入口读取公开站点配置。密钥只保存在 Worker Secrets。

## 语言入口与搜索引擎

`/` 输出完整英文首页，`/docs/` 输出完整英文文档首页。两处默认入口在浏览器中优先读取手动语言选择，否则按浏览器首选语言识别：`zh` 及其变体进入中文，其他语言使用英文。没有 JavaScript 时保留英文内容和可访问链接。

`/en/`、`/zh/` 与 `/docs/en/`、`/docs/zh/` 固定语言，不自动重定向。导航切换将选择保存在 `localStorage` 的 `a2rt.language`；存储不可用时链接仍可切换语言。英文首页 canonical 指向 `/`，中文首页指向 `/zh/`，文档逐页提供 canonical、双向 hreflang 和 x-default。sitemap 只列出对应的规范地址。

## 内容与来源

```text
protocol/                当前规范、Canvas 要求与 Realtime 契约/配置/Schema、来源记录
site/                    明亮风格官网、中英文内容和同步组示意
site.config.json         公开站点配置、草案状态和文档修订日期
docs/source/zh/          中文接入设计、示例、术语与状态
docs/source/en/          英文导读，覆盖相同的当前架构
site/partials/          官网与 Docs 共用的导航和搜索弹窗
site/assets/shell.*     共用导航样式与交互
site/assets/search.*    共用搜索与 AI 问答样式和交互
docs/theme/psdocs/       文档正文、侧栏与目录主题
worker/                  Cloudflare Worker 文档检索与问答
scripts/                 构建、配置示意检查、索引与站内检查
.github/workflows/       main 自动部署、PR 构建检查
dist/                    官网与 Docs 的统一静态产物（不提交）
```

中文概览、核心章节和当前 Canvas Profile 页面从 `protocol/` 自动生成。来源项目、提交和文件摘要记录在 `protocol/SOURCE.json`。本仓库只发布当前架构内容。英文为按同一规范编写的导读，详细规则以中文正文为准。

配置示例从第 01 章提取为 `dist/assets/architecture-example.json`。它解释时钟、同步组和轨道的关系，不是已发布的线协议格式。

## 核心边界

- 每个 epoch 唯一 `root`，子时钟和窗口精确映射到整数根刻度。
- 每轨每周期最多一个数据帧；多来源、双向、分片和重传不增加名额。
- 同步组独立推进，各接收端按 Profile 判定自己的交付条件。
- 必须且只能有一条 system 输入轨道，其分组和内容契约由 Profile 决定。
- Core 固定通用机制与资源约束；Profile 定义消费条件、领域事件与异常策略；Binding 落实通信和资源约束。
- 双向遵循谁发送谁负责：发送端准备信息并承担发送侧恢复，接收端验收；模型不拼包、不发起传输重试。
- Core 不强制错误消息或逐帧 ACK；Profile 可选择静默丢弃或通知、恢复、终止，不能伪造成功。
- 时钟、分组、策略、限额与格式在 epoch 内冻结，变更保留历史数据的解释。

## 检查

```sh
python scripts/check_protocol_docs.py
python scripts/build.py --preview
python scripts/check_site.py
npm ci --prefix worker
npm test --prefix worker
npm run check --prefix worker
```

检查覆盖来源摘要、配置示意的结构与预算算式、严格双语 Sphinx 构建、链接、公开产物凭据扫描、当前内容检索，以及 Worker 的来源、挑战验证、限流和密钥边界。Worker 测试使用模拟模型响应，不调用真实模型。

AI 索引从当前构建的 Docs 生成。`dist/docs/ai-index/` 与 `worker/assets/index/` 共享相同数据和版本记录，发布时应作为同一批产物更新。部署配置见 [DEPLOY.md](DEPLOY.md)。

## 品牌资源

`/brand/` 展示当前九宫格与四角星标志。官网与 Docs 的共用导航统一使用 `site/assets/logo-symbol.svg`。`favicon.svg` 使用适合小尺寸的描边。资源使用矢量图形，背景透明。

## 文档主题来源

文档站沿用 `proteinseek/proteinseek-workbench-docs` 的 Sphinx 主题与索引构建基础，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
