import json
import re
from typing import Any, Dict, List, Optional

from google import genai


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def gemini_recommend_products_with_reasons(
    *,
    api_key: str,
    model_name: str,
    purchased: List[Dict[str, Any]],
    catalog: List[Dict[str, Any]],
    max_items: int = 4,
    social_proof: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns list like:
    [
      {"id": 12, "reason": "Because you often buy Office accessories under $30."},
      ...
    ]

    social_proof (optional):
      {
        "also_bought_top": [{"id": 1, "name": "...", "category": "...", "count": 5}, ...],
        "top_categories_among_similar": [{"category":"Electronics","count":12}, ...],
        "note": "Use these only as supporting signals; never invent purchases."
      }
    """
    if not api_key:
        return []

    purchased_small = purchased[:20]
    catalog_small = catalog[:200]

    social_proof_payload = social_proof or {}

    prompt = f"""
You are an e-commerce recommendation engine.

Purchased products (do NOT recommend these):
{json.dumps(purchased_small, ensure_ascii=False)}

Full product catalog:
{json.dumps(catalog_small, ensure_ascii=False)}

Social proof signals from similar shoppers (optional supporting signal):
{json.dumps(social_proof_payload, ensure_ascii=False)}

Task:
Recommend up to {max_items} products the user is likely to buy next.

Rules:
- Only recommend products from the catalog.
- Do NOT recommend any purchased product.
- You MAY use social proof signals to strengthen reasons (e.g., "popular with similar shoppers"),
  but do NOT invent purchases, users, or items not provided.
- Output MUST be valid JSON ONLY (no extra text).
- Each reason must be short (<= 18 words), friendly, and based on purchase patterns and/or social proof.
- Output schema:
{{
  "recommended": [
    {{"id": <int>, "reason": "<string>"}},
    {{"id": <int>, "reason": "<string>"}}
  ]
}}
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model_name, contents=prompt)
        text = (resp.text or "").strip()
    except Exception:
        return []

    data = _extract_json_object(text)
    if not data or "recommended" not in data:
        return []

    items = data.get("recommended", [])
    if not isinstance(items, list):
        return []

    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        pid = it.get("id")
        reason = it.get("reason", "")
        try:
            pid_int = int(pid)
        except (TypeError, ValueError):
            continue
        reason_str = str(reason).strip()
        if not reason_str:
            reason_str = "Recommended based on your recent shopping patterns."
        out.append({"id": pid_int, "reason": reason_str})

    # keep unique by id, preserve order, cap
    seen = set()
    unique: List[Dict[str, Any]] = []
    for x in out:
        if x["id"] not in seen:
            seen.add(x["id"])
            unique.append(x)

    return unique[:max_items]


def gemini_recommend_product_ids(
    *,
    api_key: str,
    purchased: List[Dict[str, Any]],
    catalog: List[Dict[str, Any]],
    max_items: int = 2,
    model_name: str = "models/gemini-2.5-flash",
) -> List[int]:
    """
    Backward-compatible helper returning only ids.
    """
    items = gemini_recommend_products_with_reasons(
        api_key=api_key,
        model_name=model_name,
        purchased=purchased,
        catalog=catalog,
        max_items=max_items,
        social_proof=None,
    )
    ids: List[int] = []
    for x in items:
        try:
            ids.append(int(x.get("id")))
        except Exception:
            continue

    # unique preserve order
    out: List[int] = []
    for i in ids:
        if i not in out:
            out.append(i)
    return out[:max_items]
