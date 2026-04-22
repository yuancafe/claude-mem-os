# Claude Mem OS Bridge

> **Frankenstein integration / 缝合怪项目**  
> This repo is a glue layer that stitches **claude-mem** and **MemOS (memos-api-mcp/OpenMem API)** together.  
> 这个仓库是一个“缝合怪”中间层：把 **claude-mem** 和 **MemOS（memos-api-mcp/OpenMem API）** 拼在一起。

## What It Does / 作用
- Reads finalized `session_summaries` from local `claude-mem` SQLite.
- Syncs them into MemOS via OpenMem `/add/message`.
- Uses incremental state (`last_synced_id`) to avoid duplicate uploads.

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

