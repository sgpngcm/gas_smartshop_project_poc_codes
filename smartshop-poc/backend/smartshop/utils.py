import hashlib
import json
from typing import List, Dict, Any

def reviews_signature(reviews_compact: List[Dict[str, Any]]) -> str:
    """
    Stable signature to detect changes in reviews for a product.
    """
    raw = json.dumps(reviews_compact, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def purchase_signature(purchases_compact):
    """
    purchases_compact: list[dict] like:
    [{"name": "...", "category": "...", "price": 12.3, "qty": 1}, ...]
    """
    payload = json.dumps(purchases_compact, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
