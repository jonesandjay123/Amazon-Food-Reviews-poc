# db.py
import os, sqlite3, time
from pathlib import Path
from typing import List, Dict, Any, Tuple

DATA_DIR = Path(__file__).parent / "data"
DB_PATH  = DATA_DIR / "bbc_news.sqlite"

_CACHE_TTL = 30          # Cache expiration time in seconds
_cache: dict[str, tuple[float, List[Dict[str, Any]]]] = {}

def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} not found ‑ convert CSV first")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _cached(key: str) -> List[Dict[str, Any]] | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            return data
    return None

def execute(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    key = f"{sql}|{params}"
    if (data := _cached(key)) is not None:
        return data

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    data = [dict(r) for r in rows]
    _cache[key] = (time.time(), data)
    return data
