import re
from datetime import datetime

def normalize_name(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9 ]", "", (value or "").upper()).strip()

def normalize_date(value: str | None) -> str | None:
    if not value: return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try: return datetime.strptime(value, fmt).date().isoformat()
        except ValueError: pass
    return None

def similarity(a: str | None, b: str | None) -> int:
    a, b = normalize_name(a), normalize_name(b)
    if not a or not b: return 0
    if a == b: return 100
    at, bt = set(a.split()), set(b.split())
    token = int(100 * len(at & bt) / max(len(at | bt), 1))
    from difflib import SequenceMatcher
    seq = int(SequenceMatcher(None, a, b).ratio() * 100)
    return max(token, seq)
