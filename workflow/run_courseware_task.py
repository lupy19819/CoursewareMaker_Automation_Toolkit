#!/usr/bin/env python3
"""Compatibility wrapper for the unified workflow executor.

Do not add workflow logic here. The only supported execution entrypoint is
workflow_executor.py; this filename is kept so older docs/commands fail less
surprisingly while the workflow converges on one name.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    raise SystemExit(
        subprocess.call(
            [sys.executable, str(ROOT / "workflow" / "workflow_executor.py"), *sys.argv[1:]],
            cwd=ROOT,
        )
    )
