# Claude Mem OS Bridge（中文）

[English](./README_EN.md) | [中文](./README_CN.md)

> **缝合怪声明**  
> 这是一个有意设计的“缝合怪”集成层，用来联动三个上游仓库：
> - `claude-mem`
> - `memos-api-mcp`
> - `MemOS`

## 项目来源仓库
本项目用于连接以下三个仓库：

1. claude-mem: https://github.com/thedotmack/claude-mem
2. memos-api-mcp: https://github.com/MemTensor/memos-api-mcp
3. MemOS: https://github.com/MemTensor/MemOS

## 1. 为什么要做这个缝合怪
`claude-mem` 本地自动采集很强，但记忆容易留在本地。  
`MemOS` 跨 Agent/跨工具共享检索很强，但不会自动采集你在 Claude/Gemini 编码会话中的细粒度时间线。

这个桥接层把两者优势合并：
1. 保留本地自动记忆体验，不改习惯。
2. 把本地孤岛记忆变成可共享资产。
3. 多工具/多 Agent 复用同一份记忆。
4. 长期减少重复上下文输入带来的 token 成本。

## 2. 术语说明（Mem / SMC / MCP）
- **Mem**：`claude-mem` 本地记忆系统（SQLite + worker + hooks）。
- **SMC**：本仓库里的 Shared Memory Center（桥接守护进程 `claude-mem-os-bridge`）。
- **MCP**：`memos-api-mcp` 所在侧，给客户端/Agent 提供 MemOS 读写检索能力。

## 3. 整体链路
1. `claude-mem` hooks 自动采集本地会话。
2. 会话总结写入本地 `session_summaries` 表。
3. **SMC 桥接服务** 增量轮询并推送到 MemOS OpenMem API（`/add/message`）。
4. 其他支持 MCP 的 Agent 再从 MemOS 读取共享记忆。

## 4. 前置条件
- macOS/Linux
- Python `>=3.10`
- Node.js + `npx`
- 已安装对应 IDE/CLI：
  - Claude Code
  - Gemini CLI（可选，但已支持）
- MemOS API Key 与 User ID

## 5. 第一步 - 安装并启用 claude-mem（Mem）

安装到 Claude Code：

```bash
npx -y claude-mem install --ide claude-code
```

安装到 Gemini CLI：

```bash
npx -y claude-mem install --ide gemini-cli
```

启动 worker：

```bash
npx -y claude-mem start
npx -y claude-mem status
```

在 Claude Code 校验插件：

```bash
claude plugin list
```

预期：`claude-mem@thedotmack` 是 enabled 状态。

## 6. 第二步 - 配置 MemOS / MCP 侧

你至少需要：
- `MEMOS_API_KEY`
- `MEMOS_USER_ID`
- 可选 `MEMOS_BASE_URL`、`MEMOS_CHANNEL`

环境变量示例：

```bash
export MEMOS_API_KEY="替换成真实key"
export MEMOS_USER_ID="替换成稳定用户ID"
export MEMOS_BASE_URL="https://memos.memtensor.cn/api/openmem/v1"
export MEMOS_CHANNEL="MODELSCOPE_REMOTE"
```

可选 MCP 配置示例（`memos-api-mcp`）：

```json
{
  "mcpServers": {
    "memos-api-mcp": {
      "command": "npx",
      "args": ["-y", "@memtensor/memos-api-mcp@latest"],
      "env": {
        "MEMOS_API_KEY": "替换成真实key",
        "MEMOS_USER_ID": "替换成稳定用户ID",
        "MEMOS_CHANNEL": "MODELSCOPE_REMOTE"
      }
    }
  }
}
```

## 7. 第三步 - 安装本项目（SMC）

```bash
git clone git@github.com:yuancafe/claude-mem-os.git
cd claude-mem-os
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 8. 第四步 - 运行桥接服务

单次同步：

```bash
claude-mem-os-bridge --once
```

持续同步：

```bash
claude-mem-os-bridge --interval 60
```

## 9. 第五步 - 做成后台守护（macOS launchd）

1. 复制并编辑模板：

```bash
cp launchd/com.claude-mem-os.bridge.plist.example \
  ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist
```

2. 加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist
launchctl list | rg com.claude-mem-os.bridge
```

## 10. 如何确认已经生效

### 10.1 Mem（claude-mem）是否在跑

```bash
npx -y claude-mem status
```

### 10.2 Web 查看器端口
不要写死 `37777`，先看实际端口：

```bash
cat ~/.claude-mem/worker.pid
```

然后访问：

```text
http://localhost:<实际端口>
```

### 10.3 SMC 是否在同步
手动跑一次：

```bash
claude-mem-os-bridge --once
```

预期：
- 没有新总结时：`no new summaries`
- 有新总结时：`synced summary id=...`

### 10.4 本地总结是否存在

```bash
sqlite3 ~/.claude-mem/claude-mem.db \
  "select 'session_summaries', count(*) from session_summaries;"
```

如果是 0，说明还没产生可同步的总结。

## 11. 安全与发布规范
- 不要提交 `.env`、API Key、个人密钥文件。
- 不要把机器专属绝对路径硬编码到发布配置。
- launchd 文件只保留 `.example` 模板。

## 12. 限制
- 依赖 `claude-mem` 本地 `session_summaries` 表结构。
- 依赖 MemOS OpenMem API（`/add/message`）兼容性。
- 这是有意保持轻量的缝合层，不是替代上游系统的“全家桶”。

## 13. 许可证
MIT
