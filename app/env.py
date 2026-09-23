"""Load GEMINI_API_KEY from the repo .env even if Streamlit cwd differs.

Supports a key on the same line as GEMINI_API_KEY= or on the following line.
"""

from __future__ import annotations

import os
from functools import lru_cache

from app.paths import ROOT


def _clean(value: str) -> str:
    return (value or "").strip().strip('"').strip("'")


def _parse_env_file() -> str:
    path = ROOT / ".env"
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not line.upper().startswith("GEMINI_API_KEY"):
            continue
        _, _, rest = line.partition("=")
        rest = _clean(rest)
        if rest:
            return rest
        if index + 1 < len(lines):
            nxt = _clean(lines[index + 1])
            if nxt and not nxt.startswith("#") and "=" not in nxt:
                return nxt
    return ""


@lru_cache(maxsize=1)
def gemini_api_key() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env", override=False)
    except ImportError:
        pass
    key = _clean(os.getenv("GEMINI_API_KEY", ""))
    if key:
        return key
    key = _parse_env_file()
    if key:
        os.environ["GEMINI_API_KEY"] = key
    return key


def gemini_model() -> str:
    return _clean(os.getenv("GEMINI_MODEL", "")) or "gemini-2.5-flash"


def gemini_enabled() -> bool:
    gemini_api_key()
    flag = _clean(os.getenv("FINTRACE_SKIP_GEMINI", "")).lower()
    if flag in {"1", "true", "yes"}:
        return False
    return bool(gemini_api_key())
