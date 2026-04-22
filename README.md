# Claude Mem OS Bridge

> **Frankenstein integration / 缝合怪项目**  
> This repo is a glue layer that stitches **claude-mem** and **MemOS (memos-api-mcp/OpenMem API)** together.  
> 这个仓库是一个“缝合怪”中间层：把 **claude-mem** 和 **MemOS（memos-api-mcp/OpenMem API）** 拼在一起。

## What It Does / 作用
- Reads finalized `session_summaries` from local `claude-mem` SQLite.
- Syncs them into MemOS via OpenMem `/add/message`.
- Uses incremental state (`last_synced_id`) to avoid duplicate uploads.

## Why This Frankenstein Exists / 为什么要做这个“缝合怪”

### EN
`claude-mem` and `MemOS` each solve different halves of the problem:
- `claude-mem`: excellent automatic capture on local coding workflows.
- `MemOS`: excellent cross-agent/shared memory retrieval and cloud-scale reuse.

This bridge combines both strengths:
1. Keep local auto-capture experience unchanged.
2. Turn isolated local memory into shared memory assets.
3. Reuse memory across tools/agents instead of rebuilding context repeatedly.
4. Reduce prompt/context token waste over time.

### 中文
`claude-mem` 和 `MemOS` 各自只解决一半问题：
- `claude-mem`：本地编码场景自动记忆采集很强。
- `MemOS`：跨 Agent / 跨工具共享检索很强。

这个桥接层的价值就是把两边优势拼起来：
1. 保留本地自动采集体验，不改工作习惯。
2. 把“本地孤岛记忆”变成“可共享资产”。
3. 多个工具/Agent 复用同一份记忆，减少重复喂上下文。
4. 长期降低上下文 token 浪费。

## Architecture / 架构
1. `claude-mem` captures memory locally.
2. This bridge polls `session_summaries`.
3. Bridge pushes records to MemOS cloud/self-host endpoint.

## Install / 安装

```bash
git clone git@github.com:yuancafe/claude-mem-os.git
cd claude-mem-os
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configure / 配置

Copy `.env.example` and export variables:

```bash
cp .env.example .env
```

Required:
- `MEMOS_API_KEY`
- `MEMOS_USER_ID`

Optional:
- `MEMOS_BASE_URL` (default: `https://memos.memtensor.cn/api/openmem/v1`)
- `MEMOS_CHANNEL` (default: `MODELSCOPE_REMOTE`)

Example:

```bash
export MEMOS_API_KEY="your_key"
export MEMOS_USER_ID="your_user_id"
export MEMOS_BASE_URL="https://memos.memtensor.cn/api/openmem/v1"
export MEMOS_CHANNEL="MODELSCOPE_REMOTE"
```

## Run / 运行

One-time sync:

```bash
claude-mem-os-bridge --once
```

Continuous sync:

```bash
claude-mem-os-bridge --interval 60
```

## Background Service (macOS launchd) / 后台守护（macOS）

1. Edit `launchd/com.claude-mem-os.bridge.plist.example`.
2. Copy to `~/Library/LaunchAgents/com.claude-mem-os.bridge.plist`.
3. Load:

```bash
launchctl unload ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist
```

## Security Notes / 安全说明
- This repo does **not** contain your API keys.
- This repo does **not** contain hardcoded personal absolute paths.
- Do not commit `.env`, logs, or local secret files.

## Limitations / 限制
- Depends on `claude-mem` local DB schema (`session_summaries`).
- Depends on MemOS OpenMem API compatibility (`/add/message`).
- It is intentionally a lightweight glue project (Frankenstein style), not a full replacement of either upstream project.

## Upstream Projects / 上游项目
- claude-mem: https://github.com/thedotmack/claude-mem
- memos-api-mcp: https://github.com/MemTensor/memos-api-mcp
- MemOS: https://github.com/MemTensor/MemOS

## License
MIT
