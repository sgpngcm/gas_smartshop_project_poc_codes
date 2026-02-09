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


def generate_product_review_digest(
    *,
    api_key: str,
    model_name: str,
    product: Dict[str, Any],
    reviews: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Returns:
    {
      "highlights": ["...", "..."],
      "sample_reviews": [{"rating": 5, "title": "...", "body": "..."}, ...]
    }

    IMPORTANT: sample_reviews are AI-generated and must be labeled as such in the UI.
    """
    if not api_key:
        return {"highlights": [], "sample_reviews": []}

    # Keep prompt small
    reviews_small = reviews[:30]
    product_small = {
        "name": product.get("name"),
        "category": product.get("category"),
        "price": product.get("price"),
        "ai_short_description": product.get("ai_short_description", ""),
        "ai_review_summary": product.get("ai_review_summary", ""),
    }

    prompt = f"""
You are SmartShop's product reviewer assistant.

PRODUCT:
{json.dumps(product_small, ensure_ascii=False)}

REAL USER REVIEWS (rating/title/body). If empty, rely only on product fields:
{json.dumps(reviews_small, ensure_ascii=False)}

Task:
1) Write 4-6 "review highlights" bullets grounded in provided info.
2) Create 2-3 clearly AI-generated "sample reviews" (helpful examples), grounded in provided info.

Rules:
- Do NOT invent features not present in product fields or user reviews.
- If reviews are empty, be conservative and only reflect product fields.
- Highlights must be short and practical.
- Sample reviews must look realistic but MUST NOT claim to be real users.
- Output JSON ONLY. No extra text.

Schema:
{{
  "highlights": ["...", "..."],
  "sample_reviews": [
    {{"rating": 5, "title": "...", "body": "..."}},
    {{"rating": 4, "title": "...", "body": "..."}}
  ]
}}
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model_name, contents=prompt)
        data = _extract_json_object((resp.text or "").strip())
    except Exception:
        return {"highlights": [], "sample_reviews": []}

    if not isinstance(data, dict):
        return {"highlights": [], "sample_reviews": []}

    highlights = data.get("highlights") if isinstance(data.get("highlights"), list) else []
    sample_reviews = data.get("sample_reviews") if isinstance(data.get("sample_reviews"), list) else []

    # Basic cleanup
    highlights_out = [str(x).strip() for x in highlights if str(x).strip()][:6]

    samples_out: List[Dict[str, Any]] = []
    for it in sample_reviews[:3]:
        if not isinstance(it, dict):
            continue
        try:
            rating = int(it.get("rating", 5))
        except Exception:
            rating = 5
        rating = max(1, min(rating, 5))
        title = str(it.get("title", "")).strip()[:80]
        body = str(it.get("body", "")).strip()[:400]
        if not body and not title:
            continue
        samples_out.append({"rating": rating, "title": title, "body": body})

    return {"highlights": highlights_out, "sample_reviews": samples_out}
