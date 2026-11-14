# A2RT — Agent-to-Real-Time Protocol

A2RT 是智能体与实时环境之间的多模态交互协议。六条逻辑轨道独立更新，事件与真实执行回执保持因果关联；Profile 声明领域能力和执行策略。

**当前状态：0.2 草案。** 仓库提供规范、JSON Schema、消息示例、文档校验器，以及介绍网站。它不是生产 SDK，也没有硬实时截止保证。

目标站点：[www.a2rt.org](https://www.a2rt.org/) · [Docs](https://www.a2rt.org/docs/)

## 本地运行

需要 Python 3.11+。Worker 开发和校验另需 Node.js 22+。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:4173/`。Windows 虚拟环境使用 `.venv\Scripts\Activate.ps1`。
只预览官网排版可运行 `python scripts/build.py --home-only`；完整 Docs 和 AI 索引需要完整构建。

## 仓库结构

```text
site/                    官网模板、中英文内容、样式与交互
site.config.json         公开的站点配置，不含密钥
protocol/                0.2 规范、schemas、examples、校验器
docs/
  source/zh/             中文介绍与入门文档
  source/en/             英文导读
  theme/psdocs/          从指定文档仓库引入并改造的 Sphinx 主题
  conf.py                文档构建与公开 AI 入口配置
worker/                  Cloudflare Worker 文档检索与问答
scripts/                 构建、索引生成、站内链接检查
.github/workflows/      main 自动部署、PR 构建检查
dist/                    官网与文档的统一静态产物（不提交）
```

中文核心规范章节在构建时直接由 `protocol/01-*.md` 至 `05-*.md` 生成。
修改规范时编辑 `protocol/`，不用重复维护一份中文页面。英文是独立维护的导读，页面已说明其范围。

官网首页支持中文和英文；Docs 根目录提供语言选择，正文在 `/docs/zh/` 与 `/docs/en/`。
本地全文搜索无需模型 API。没有配置 AI 接口时，AI 操作入口隐藏，普通搜索仍可正常使用。

## Logo 与品牌资源

本地打开 `/brand/` 查看字标、单色版本与小尺寸图标，可直接下载透明 SVG。
`site/assets/logo.svg` 用于深色背景，`logo-dark.svg` 用于浅色背景；`mark.svg` 和
`mark-dark.svg` 是独立图形，`favicon.svg` 用于浏览器图标。
所有字形均为矢量路径，不依赖字体。修改 `scripts/build_brand.py` 后运行
`python scripts/build_brand.py`，会同步生成官网及文档站资产，再运行完整网站构建。

## 检查

```sh
python protocol/validate_examples.py
python scripts/build.py
python scripts/check_site.py
npm ci --prefix worker
npm test --prefix worker
npm run check --prefix worker
```

检查覆盖协议正反例、严格 Sphinx 构建、站内链接和锚点、公开产物凭据扫描，以及 Worker 的来源、挑战验证、限流、请求大小和密钥边界。Worker 单元测试使用本地模拟响应，不调用真实模型。

## 部署

见 [DEPLOY.md](DEPLOY.md)。推送到 `main` 后，GitHub Actions 构建并发布官网与 Docs。域名未绑定时，构建会使用 Pages 提供的 `/a2rt` 基础路径；绑定 `www.a2rt.org` 后使用 `/`。

AI 与 Cloudflare 自动发布均默认关闭。配置完成后再开启，模型 API key 仅放在 Worker Secrets。

## 来源

文档站沿用 `proteinseek/proteinseek-workbench-docs` 的 Sphinx 主题与索引构建逻辑，并替换为 A2RT 的内容、品牌、导航及 Worker 接口。未引入上游 Git 历史、密钥或旧部署脚本，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 参与

通过 [Issues](https://github.com/a2rt-project/a2rt/issues) 讨论规范和适配需求。涉及协议变更时，请一并更新 Schema、示例、校验器和相应文档，并说明兼容性影响。
