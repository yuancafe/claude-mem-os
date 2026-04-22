# Claude Mem OS Bridge

[English](./README.md) | [简体中文](./README_ZH.md)

> **Frankenstein integration notice**  
> This project is intentionally a glue layer that stitches three upstream repositories together:
> - `claude-mem`
> - `memos-api-mcp`
> - `MemOS`

## Source Repositories (Top-Level)
This project explicitly connects these three repositories:

1. claude-mem: https://github.com/thedotmack/claude-mem
2. memos-api-mcp: https://github.com/MemTensor/memos-api-mcp
3. MemOS: https://github.com/MemTensor/MemOS

## 1. Why This Frankenstein Exists
`claude-mem` is great at local automatic capture, but memory stays local.  
`MemOS` is great at shared/cross-agent retrieval, but does not automatically capture your Claude/Gemini coding timeline by itself.

This bridge gives you both:
1. Keep local auto-capture workflow unchanged.
2. Convert isolated local memory into shared memory assets.
3. Reuse memory across tools/agents.
4. Reduce repeated context-token costs over time.

## 2. Terminology (Mem / SMC / MCP)
- **Mem**: `claude-mem` local memory system (SQLite + worker + hooks).
- **SMC**: Shared Memory Center in this repo (the bridge daemon `claude-mem-os-bridge`).
- **MCP**: `memos-api-mcp` side, used by clients/agents for querying and writing MemOS memory.

## 3. End-to-End Architecture
1. `claude-mem` hooks capture your session timeline locally.
2. Summaries are written to local table `session_summaries`.
3. **SMC bridge** polls incrementally and pushes new summaries to MemOS OpenMem API (`/add/message`).
4. Other MCP-enabled agents query shared memory via MemOS.

## 4. Prerequisites
- macOS/Linux
- Python `>=3.10`
- Node.js + `npx`
- Installed IDE/CLI:
  - Claude Code
  - Gemini CLI (optional but supported)
- MemOS API key and user id

## 5. Step A - Install and Enable claude-mem (Mem)

Install for Claude Code:

```bash
npx -y claude-mem install --ide claude-code
```

Install for Gemini CLI:

```bash
npx -y claude-mem install --ide gemini-cli
```

Start worker:

```bash
npx -y claude-mem start
npx -y claude-mem status
```

Check plugin load in Claude Code:

```bash
claude plugin list
```

Expected: `claude-mem@thedotmack` should be enabled.

## 6. Step B - Configure MemOS / MCP Side

You need:
- `MEMOS_API_KEY`
- `MEMOS_USER_ID`
- optional `MEMOS_BASE_URL` and `MEMOS_CHANNEL`

Example environment:

```bash
export MEMOS_API_KEY="replace_with_real_key"
export MEMOS_USER_ID="replace_with_stable_user_id"
export MEMOS_BASE_URL="https://memos.memtensor.cn/api/openmem/v1"
export MEMOS_CHANNEL="MODELSCOPE_REMOTE"
```

Optional MCP server config example (`memos-api-mcp`):

```json
{
  "mcpServers": {
    "memos-api-mcp": {
      "command": "npx",
      "args": ["-y", "@memtensor/memos-api-mcp@latest"],
      "env": {
        "MEMOS_API_KEY": "replace_with_real_key",
        "MEMOS_USER_ID": "replace_with_stable_user_id",
        "MEMOS_CHANNEL": "MODELSCOPE_REMOTE"
      }
    }
  }
}
```

## 7. Step C - Install This Bridge (SMC)

```bash
git clone git@github.com:yuancafe/claude-mem-os.git
cd claude-mem-os
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 8. Step D - Run the Bridge

One-time sync:

```bash
claude-mem-os-bridge --once
```

Continuous daemon mode:

```bash
claude-mem-os-bridge --interval 60
```

## 9. Step E - Make It Persistent (launchd on macOS)

1. Copy and edit template:

```bash
cp launchd/com.claude-mem-os.bridge.plist.example \
  ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist
```

2. Load:

```bash
launchctl unload ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.claude-mem-os.bridge.plist
launchctl list | rg com.claude-mem-os.bridge
```

## 10. How to Verify It Is Working

### 10.1 Mem (`claude-mem`) is active

```bash
npx -y claude-mem status
```

### 10.2 Web viewer endpoint
Do not assume port `37777`. Check actual port from:

```bash
cat ~/.claude-mem/worker.pid
```

Then open:

```text
http://localhost:<actual_port>
```

### 10.3 Bridge (SMC) is syncing
Run:

```bash
claude-mem-os-bridge --once
```

Expected:
- `no new summaries` (if none yet), or
- `synced summary id=...`

### 10.4 Local DB data check

```bash
sqlite3 ~/.claude-mem/claude-mem.db \
  "select 'session_summaries', count(*) from session_summaries;"
```

If count is zero, sync cannot upload summaries yet.

## 11. Security and Publishing Rules
- Never commit `.env`, API keys, or personal secret files.
- Never hardcode machine-specific absolute paths in distributed configs.
- Keep launchd files as `.example` templates only.

## 12. Limitations
- Depends on `claude-mem` local schema (`session_summaries`).
- Depends on MemOS OpenMem API compatibility (`/add/message`).
- This is a glue project by design, not a full replacement for either upstream.

## 13. License
MIT
