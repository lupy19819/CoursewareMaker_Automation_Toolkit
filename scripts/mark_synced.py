#!/usr/bin/env python3
"""
mark_synced.py
--------------
将 output/upload_log.jsonl 中所有未同步的条目标记为 synced=true。
在 agent 完成 yach_doc_append 之后调用。

用法：
    python3 scripts/mark_synced.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "output" / "upload_log.jsonl"


def main():
    if not LOG_FILE.exists():
        print("No log file found.")
        return

    entries = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    marked = 0
    for e in entries:
        if not e.get("synced"):
            e["synced"] = True
            marked += 1

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Marked {marked} entries as synced.")


if __name__ == "__main__":
    main()
