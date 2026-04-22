#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_BASE_URL = "https://memos.memtensor.cn/api/openmem/v1"
DEFAULT_CHANNEL = "MODELSCOPE_REMOTE"


def _load_state(path: Path) -> Dict[str, int]:
    if not path.exists():
        return {"last_synced_id": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"last_synced_id": 0}


def _save_state(path: Path, state: Dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _fetch_rows(db_path: Path, last_id: int, limit: int = 50) -> List[Tuple]:
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              id,
              memory_session_id,
              project,
              request,
              investigated,
              learned,
              completed,
              next_steps,
              notes,
              created_at
            FROM session_summaries
            WHERE id > ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (last_id, limit),
        )
        return cur.fetchall()
    finally:
        conn.close()


def _build_summary(row: Tuple) -> str:
    row_id, memory_session_id, project, request, investigated, learned, completed, next_steps, notes, created_at = row
    parts = [
        f"[claude-mem sync] summary_id={row_id}",
        "source_tool=claude-code",
        f"session={memory_session_id}",
        f"project={project or 'unknown'}",
        f"created_at={created_at}",
    ]
    if request:
        parts.append(f"request: {request}")
    if investigated:
        parts.append(f"investigated: {investigated}")
    if learned:
        parts.append(f"learned: {learned}")
    if completed:
        parts.append(f"completed: {completed}")
    if next_steps:
        parts.append(f"next_steps: {next_steps}")
    if notes:
        parts.append(f"notes: {notes}")
    return "\n".join(parts)


def _conversation_id(user_id: str, conversation_first_message: str) -> str:
    raw = f"{user_id}\n{conversation_first_message}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _post_add_message(
    base_url: str,
    api_key: str,
    source: str,
    user_id: str,
    conversation_first_message: str,
    created_at: str,
    summary_text: str,
) -> None:
    conv_id = _conversation_id(user_id, conversation_first_message)
    payload = {
        "user_id": user_id,
        "conversation_id": conv_id,
        "messages": [
            {"role": "user", "content": conversation_first_message, "chat_time": created_at},
            {"role": "assistant", "content": summary_text, "chat_time": created_at},
        ],
        "source": source,
    }
    req = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/add/message",
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Token {api_key}"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status < 200 or resp.status >= 300:
            raise RuntimeError(f"HTTP {resp.status}")
        _ = resp.read()


def run_once(
    db_path: Path,
    state_path: Path,
    base_url: str,
    api_key: str,
    user_id: str,
    channel: str,
) -> int:
    if not db_path.exists():
        print(f"[bridge] db not found: {db_path}", file=sys.stderr)
        return 1

    state = _load_state(state_path)
    last_id = int(state.get("last_synced_id", 0))
    rows = _fetch_rows(db_path, last_id)
    if not rows:
        print("[bridge] no new summaries")
        return 0

    synced = 0
    for row in rows:
        row_id = int(row[0])
        session_id = row[1] or f"summary-{row_id}"
        created_at = row[9] or ""
        first_msg = f"claude-mem::{session_id}"
        summary_text = _build_summary(row)
        try:
            _post_add_message(
                base_url=base_url,
                api_key=api_key,
                source=channel,
                user_id=user_id,
                conversation_first_message=first_msg,
                created_at=created_at,
                summary_text=summary_text,
            )
            state["last_synced_id"] = row_id
            _save_state(state_path, state)
            synced += 1
            print(f"[bridge] synced summary id={row_id}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"[bridge] HTTP error id={row_id}: {e.code} {body}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"[bridge] sync error id={row_id}: {e}", file=sys.stderr)
            return 2

    print(f"[bridge] done, synced={synced}, last_id={state.get('last_synced_id', last_id)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync claude-mem session summaries to MemOS.")
    parser.add_argument("--db-path", default=str(Path.home() / ".claude-mem" / "claude-mem.db"))
    parser.add_argument("--state-path", default=str(Path.home() / ".claude-mem" / "memos-sync-state.json"))
    parser.add_argument("--interval", type=int, default=30, help="Polling interval seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    api_key = os.environ.get("MEMOS_API_KEY", "").strip()
    user_id = os.environ.get("MEMOS_USER_ID", "").strip()
    base_url = os.environ.get("MEMOS_BASE_URL", DEFAULT_BASE_URL).strip()
    channel = os.environ.get("MEMOS_CHANNEL", DEFAULT_CHANNEL).strip().upper() or DEFAULT_CHANNEL

    if not api_key:
        print("[bridge] MEMOS_API_KEY is required", file=sys.stderr)
        return 1
    if not user_id:
        print("[bridge] MEMOS_USER_ID is required", file=sys.stderr)
        return 1

    db_path = Path(args.db_path)
    state_path = Path(args.state_path)

    if args.once:
        return run_once(db_path, state_path, base_url, api_key, user_id, channel)

    while True:
        code = run_once(db_path, state_path, base_url, api_key, user_id, channel)
        time.sleep(max(5, args.interval) if code != 0 else args.interval)


if __name__ == "__main__":
    raise SystemExit(main())

