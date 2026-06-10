"""
Vercel serverless entry — exports the FastAPI ASGI app.
https://vercel.com/docs/functions/runtimes/python
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from weaver.api.main import app  # noqa: E402

__all__ = ["app"]
