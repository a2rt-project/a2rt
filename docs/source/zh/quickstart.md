# 快速入门

本页帮助你阅读和校验协议，不会启动生产运行时。

## 1. 获取协议仓库

```sh
git clone https://github.com/a2rt-project/a2rt.git
cd a2rt
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

使用 Python 3.11 或更新版本。Windows 激活虚拟环境的命令为 `.venv\Scripts\Activate.ps1`。

## 2. 运行文档示例校验

```sh
python protocol/validate_examples.py
```

校验器检查 JSON Schema、清单资源哈希、事件与回执关联、来源绑定、执行窗口和关键反例。通过意味着文档示例满足这些检查，不代表网络、媒体或真实执行器已经验收。

## 3. 读一个完整会话

按顺序打开以下文件：

1. `protocol/examples/counter.profile.json`：计数器的领域能力和执行策略。
2. `protocol/examples/session.json`：来源、stream、时钟和所选 Profile 的会话清单。
3. `protocol/examples/streaming-session.json`：同一次操作中的多个事件、独立音频和批量回执。

会话先协商清单，再交付 `feedback_seq=0` 的初始反馈 F0。每条消息引用一致的 `session_id`、`epoch` 和 `manifest_id`。

## 4. 跟踪两种计数

**事件在途数**：已经发送、尚未获得首个真实 `core.result` 的事件数量。

**活动操作数**：已经预占、尚未确认终结的操作数量。

两者分别受 Profile 限制。同一个操作可以包含 `begin → update → end` 多条事件。收到 `accepted` 可以释放该事件的在途名额，但不会结束操作；发出 `end` 也不等于清理已经完成。

## 5. 为你的环境制定 Profile

列出领域事件与 payload Schema、状态 Schema、工具能力、具名执行策略及依赖规则，再定义适配器的真实执行和恢复职责。不要仅修改示例的协议字符串或计数器名称就宣称适配完成。

继续阅读[核心与 Profile](spec/01-core-and-profiles.md)、[执行与恢复](spec/04-execution-and-recovery.md)及[示例说明](examples.md)。
