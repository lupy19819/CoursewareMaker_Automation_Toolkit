#!/usr/bin/env python3
"""
sync_uploads_to_sheet.py
------------------------
读取 output/upload_log.jsonl 中尚未同步的条目，
格式化后输出 Markdown 表格行，供 OpenClaw agent 调用 yach_doc_append 追加到石墨表格。

用法（由 agent 调用）：
    python3 scripts/sync_uploads_to_sheet.py

输出：
    - 如果有待同步条目：打印 JSON 结构
        {
          "sheet_url": "...",
          "rows": [...],          # 可直接追加的行内容
          "pending_count": N
        }
    - 如果无待同步条目：打印 {"pending_count": 0}

同步完成后由 agent 将 log 中对应条目的 synced 标为 true。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "output" / "upload_log.jsonl"
SHEET_URL = "https://yach-doc-shimo.zhiyinlou.com/sheets/47kgJmVE1gS1BOqV/Xwvzy"

# 石墨表格字段顺序（与现有表头对齐）
COLUMNS = ["id", "name", "category", "url", "desc", "topic", "tag", "type", "creator", "updatedAt"]


def format_cell(val):
    if isinstance(val, list):
        return ",".join(str(v) for v in val)
    if val is None:
        return ""
    return str(val)


def main():
    if not LOG_FILE.exists():
        print(json.dumps({"pending_count": 0}))
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

    pending = [e for e in entries if not e.get("synced")]
    if not pending:
        print(json.dumps({"pending_count": 0}))
        return

    rows = []
    for e in pending:
        cells = [format_cell(e.get(col, "")) for col in COLUMNS]
        rows.append("\t".join(cells))

    result = {
        "sheet_url": SHEET_URL,
        "rows": rows,
        "pending_count": len(pending),
        "log_file": str(LOG_FILE),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
