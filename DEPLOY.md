# 部署 A2RT 官网与文档

默认目标是 `https://www.a2rt.org/`，文档入口是 `/docs/`。浏览器只读取静态页面；AI 问答由独立 Cloudflare Worker 提供。

当前后端为 `a2rt-docs-ai`，公开接口地址为 `https://a2rt-docs-ai.zmgithub.workers.dev/api/ai-qa/chat`。
模型配置为 DeepSeek 的 `deepseek-flash`，调用 `https://api.deepseek.com/chat/completions`，关闭思考模式以将小额输出预算用于文档回答。
当前生产配置已启用 AI；两项私密密钥仅保存在 Cloudflare Worker Secrets 中。
后续如绑定 `api.a2rt.org`，同步更新站点的 `ai_endpoint` 或 Actions 的 `DOCS_AI_ENDPOINT` 即可。

## 1. GitHub Pages

在 `a2rt-project/a2rt` 的 **Settings → Pages** 中，将 **Source** 设置为 **GitHub Actions**。

仓库的 `.github/workflows/deploy-pages.yml` 在推送到 `main` 时运行，也支持 Actions 页面手动触发。手动发布也必须选择 `main`；其他分支只构建，不部署。

构建过程：

1. 校验协议示例。
2. 生成官网、中英文 Docs 和 AI 文档索引。
3. 检查链接、锚点、公开产物及 Worker 行为。
4. 将 `dist/` 作为一个 Pages artifact 发布。
5. 仅在明确启用后，同步发布对应的 Worker 与索引。

PR 工作流分别检查根路径 `/` 和项目路径 `/a2rt/`，不会发布网站。

### 首次推送本地代码

先检查本地改动并创建提交，然后将当前分支推送到远程 `main`。不要覆盖远程已有提交；若仓库已经有 README 等初始提交，先 fetch 并整合历史。

```sh
git status
git add .
git commit -m "Build A2RT protocol website and documentation"
git push -u origin HEAD:main
```

作者信息使用仓库本地 Git 配置，不必修改全局身份。

## 2. 域名和 HTTPS

先在 **Settings → Pages → Custom domain** 填入 `www.a2rt.org` 并保存，再到 DNS 服务商添加：

| 类型 | 主机记录 | 值 |
| --- | --- | --- |
| CNAME | www | a2rt-project.github.io |

DNS 校验与证书签发完成后开启 **Enforce HTTPS**。若通过 Cloudflare 管理 `www` 的解析，初始连接 GitHub Pages 时可使用 DNS only，便于 Pages 校验和证书签发。

Pages 工作流读取 `configure-pages` 输出的 host 和 base path，并使用 HTTPS 生成站点地址，因此在域名未绑定时，也可部署到 `https://a2rt-project.github.io/a2rt/`。这也避免自定义域名等待证书时，Pages 返回 HTTP 地址导致构建失败。绑定或变更域名后重新运行工作流，以同步 canonical URL、资源路径与 sitemap。

`dist/CNAME` 只记录构建目标；使用 Actions 发布时，它不能代替 GitHub Pages 设置中的域名绑定。

参考：[GitHub Pages 自定义域名](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)。

## 3. 首次部署 AI Worker

先完成一次完整网站构建，再运行：

```sh
npm ci --prefix worker
cd worker
npx wrangler login
npm run deploy
```

在新账号首次部署时，先将 `AI_QA_ENABLED` 改为字符串 `false`，避免配置完成前产生模型调用。健康检查路径为 `/api/ai-qa/healthz`，尚未配置时返回 `configured: false`。

在 Worker 的 **Settings → Variables and Secrets** 中添加两个 **Secret**：

| Secret 名称 | 内容 |
| --- | --- |
| `AI_QA_API_KEY` | 模型提供商的新 API key |
| `TURNSTILE_SECRET_KEY` | Turnstile widget 的 secret key |

也可以在 `worker/` 目录中用交互输入设置，命令参数不包含密钥值：

```sh
npx wrangler secret put AI_QA_API_KEY
npx wrangler secret put TURNSTILE_SECRET_KEY
```

不要将模型密钥写入站点 JSON、前端环境变量、`.github` 工作流、索引文件或 Wrangler 的 `vars`。本地调试可以使用被 Git 忽略的 `worker/.dev.vars`。

## 4. Turnstile 与模型参数

当前项目已接入现有 Turnstile widget，无需重新创建。迁移到新账号时，为 widget 允许 hostname `www.a2rt.org`。前端会按需加载 widget，并使用 action `docs_qa`；Worker 验证 success、hostname 和 action。Site key 可以公开，secret key 必须只存 Worker。

编辑 `worker/wrangler.jsonc` 的普通变量：

| 变量 | 配置 |
| --- | --- |
| `AI_QA_ENABLED` | 全部配置就绪后设为字符串 `true` |
| `AI_QA_BASE_URL` | 支持 Chat Completions 的 HTTPS 接口基址，如 `https://api.deepseek.com`；也可填写完整 `/chat/completions` 地址 |
| `AI_QA_MODEL` | 你的账号可用的具体模型 ID |
| `ALLOWED_ORIGIN` | `https://www.a2rt.org`，不带尾部斜杠 |
| `AI_QA_DOCS_URL_PREFIX` | `https://www.a2rt.org/docs` |

此实现使用普通 JSON 响应，固定 `stream=false`，不支持把 Anthropic 或 Responses 等不同协议的地址直接填入。若提供商不支持 `max_tokens`，需要相应调整 Worker 的请求格式。

配置文件是普通变量的来源；不要只在控制台修改同名普通变量后期待下一次部署仍保留。Secrets 则独立保存在 Cloudflare。

设置好 Secrets 并编辑上述变量后，在 `worker/` 目录再次运行 `npm run deploy`，让开关与模型参数生效。
将 `wrangler.jsonc` 中的公开配置修改提交到 `main`，以便后续自动部署使用相同配置。
健康检查的 `configured: true` 只表示必需配置齐全；真实模型连通性需在第 6 步通过文档问答验证。

Worker 使用 Rate Limiting binding，每 IP 每 60 秒近似限制 10 次；这是防滥用限制，不是全局精确预算。多个 Worker 共用账号时，请为 `namespace_id` 选择不冲突的数字。另有限制：请求体 16 KiB、问题 1200 字符、模型输出 1024 token、模型调用 30 秒超时。

应用代码不记录问题、答案或密钥；模型提供商与托管平台的数据处理仍受各自设置约束。

参考：[Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)、[Turnstile 服务端验证](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)、[Rate Limiting](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)。

## 5. Worker 域名

`a2rt.org` 的 Zone 在 Cloudflare 激活后，在 Worker 的 **Settings → Domains & Routes → Add → Custom Domain** 中绑定 `api.a2rt.org`。Cloudflare 会建立该主机的 DNS 记录。

若希望把域名绑定也纳入代码，可在 `worker/wrangler.jsonc` 增加：

```json
"routes": [
  { "pattern": "api.a2rt.org", "custom_domain": true }
]
```

在 Zone 尚未接入 Cloudflare 时，可先使用首次部署得到的 `workers.dev` 地址。不要通过将整个 `www.a2rt.org` 绑定到 Worker 的方式覆盖 GitHub Pages。

参考：[Worker Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)。

## 6. 在 Docs 中启用 AI

`site.config.json` 已保存当前 Worker 的公开接口与 Turnstile site key，Pages 构建会直接使用它们。若要覆盖配置，在 GitHub **Settings → Secrets and variables → Actions → Variables** 中设置：

| Variable | 值 |
| --- | --- |
| `DOCS_AI_ENDPOINT` | `https://a2rt-docs-ai.zmgithub.workers.dev/api/ai-qa/chat`（绑定自定义域名后可替换） |
| `TURNSTILE_SITE_KEY` | Turnstile 的公开 site key |

重新运行 Pages 工作流，文档搜索面板就会显示 AI 问答入口。没有这两个公开配置时，站点只提供本地全文搜索，不会尝试发送模型请求。

非空的 Actions Variables 会优先覆盖 `ai_endpoint` 与 `turnstile_site_key`；未设置或空白的变量保留文件中的公开配置。
要隐藏 AI 入口，清空 Actions 的 endpoint 以及文件中的 `ai_endpoint`。

该组件用于 Docs 问答，action 固定为 `docs_qa`，生产后端只接受 `www.a2rt.org` hostname。浏览器请求结束或关闭面板会重置组件，重试获取新 token；Worker 每次向 Siteverify 验证后才调用模型。
单元测试模拟重复 token 被拒绝；上线验收还需用真实组件验证一次成功提交，再确认重放同一 token 返回 `CHALLENGE_FAILED`。未完成这一步不能视为真实链路验证成功。

通过 UI 提交一个 A2RT 问题，确认返回答案和 `/docs/` 来源链接。密钥不应出现在浏览器请求、HTML 或 JavaScript 中。CORS 不是身份验证，不能代替 Turnstile 与限流。

## 7. 可选：main 同步部署 Worker

完成手动配置后，在 GitHub 设置：

| 类型 | 名称 | 内容 |
| --- | --- | --- |
| Secret | `CLOUDFLARE_API_TOKEN` | 仅目标账号所需 Worker 发布权限的 token |
| Variable | `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账号 ID |
| Variable | `DEPLOY_AI_WORKER` | 字符串 `true` |

使用 Cloudflare 的 **Edit Cloudflare Workers** token 模板，并收窄到目标账号；若工作流还管理自定义域名，需要对应 Zone 权限。
这里的 token 是部署凭据，不是模型 API key。模型 key 不需要提供给 GitHub。

每次 `main` 发布时，工作流先部署 Pages，再部署同一次构建的 Worker 索引。没有 `DEPLOY_AI_WORKER=true` 时，Cloudflare 发布任务完全跳过；Pages 不依赖 Cloudflare 凭据。

## 回滚与故障定位

- 构建失败：查看 Actions 中的 Sphinx、协议校验或链接检查输出；失败构建不会发布。
- AI 尚未配置：保持 endpoint 为空，普通文档搜索继续可用。
- AI 403：检查 Origin、Turnstile hostname/action 与 token 是否有效。
- AI 429：命中请求限流，稍后重试。
- AI 503：检查开启开关、两项 Secret、模型 ID、索引及 Rate Limiting binding。
- AI 502：检查服务端模型地址、模型权限和提供商响应。Worker 不向浏览器回传原始错误内容。
- 回滚网站：回退 `main` 到已知良好的内容提交，再触发部署。Worker 单独回滚时，也要使用对应版本的文档索引。
