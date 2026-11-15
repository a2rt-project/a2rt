# A2RT — Agent-to-Real-Time Protocol

A2RT 定义智能体与实时环境之间的信息承载与同步组织机制。标准根时钟提供共同刻度与容量，子时钟组织节拍，信息同步组组织窗口，自定义轨道承载角色、方向与内容格式。

**当前状态：2026-11-16 架构设计草案。** 对应的新线协议版本、完整机器定义与运行时尚未发布。配置示例用于说明设计；文档检查不代表运行时一致性验证。

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

## 内容与来源

```text
protocol/                当前四章中文规范、Canvas 适配要求、来源记录
site/                    明亮风格官网、中英文内容和同步组示意
site.config.json         公开站点配置、草案状态和文档修订日期
docs/source/zh/          中文概览、接入设计、示例、术语与状态
docs/source/en/          英文导读，覆盖相同的当前架构
docs/theme/psdocs/       文档主题和搜索界面
worker/                  Cloudflare Worker 文档检索与问答
scripts/                 构建、配置示意检查、索引与站内检查
.github/workflows/       main 自动部署、PR 构建检查
dist/                    官网与 Docs 的统一静态产物（不提交）
```

中文核心章节和 Canvas 页面从 `protocol/` 自动生成。来源项目、提交和文件摘要记录在 `protocol/SOURCE.json`。本仓库只发布当前架构内容。英文为按同一规范编写的导读，详细规则以中文正文为准。

配置示例从第 01 章提取为 `dist/assets/architecture-example.json`。它解释时钟、同步组和轨道的关系，不是已发布的线协议格式。

## 核心边界

- 每个 epoch 唯一 `root`，子时钟和窗口精确映射到整数根刻度。
- 每轨每周期最多一个数据帧；多来源、双向、分片和重传不增加名额。
- 同步组独立推进，各接收端按 Profile 判定自己的交付条件。
- 必须且只能有一条 system 输入轨道，其分组和内容契约由 Profile 决定。
- Core 固定通用机制与资源约束；Profile 定义播放、恢复、完整性、内容校验及领域事件。
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

`/brand/` 展示当前九宫格与四角星标志。官网使用 `site/assets/logo-symbol.svg`，文档使用 `docs/static/logo-symbol.svg`，两处保持一致。`favicon.svg` 使用适合小尺寸的描边。资源使用矢量图形，背景透明。

## 文档主题来源

文档站沿用 `proteinseek/proteinseek-workbench-docs` 的 Sphinx 主题与索引构建基础，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
