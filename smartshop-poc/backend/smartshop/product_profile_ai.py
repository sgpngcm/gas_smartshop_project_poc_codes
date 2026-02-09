import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from google import genai

def _sig(name: str, category: str, price: float, reviews: List[Dict[str, Any]]) -> str:
    raw = json.dumps(
        {"name": name, "category": category, "price": price, "reviews": reviews},
        ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()
    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def generate_product_profile(
    *,
    api_key: str,
    model_name: str,
    product: Dict[str, Any],
    reviews: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Returns:
    {
      short_description: str,
      use_cases: [str],
      features: [str],
      keywords: [str],
      audience: [str],
      pros: [str],
      cons: [str],
      review_summary: str
    }
    """
    if not api_key:
        return {}

    # keep prompt small
    reviews_small = reviews[:8]

    prompt = f"""
You are generating a product profile for an e-commerce catalog search system.

PRODUCT:
{json.dumps(product, ensure_ascii=False)}

BUYER REVIEWS (short):
{json.dumps(reviews_small, ensure_ascii=False)}

Task:
Create a concise structured profile to improve search + recommendations.

Rules:
- DO NOT invent features not implied by name/category or reviews.
- Be helpful but grounded.
- Use short phrases, not long paragraphs.
- Output MUST be valid JSON ONLY.

Schema:
{{
  "short_description": "<1-2 sentences>",
  "use_cases": ["<use case>", "..."],
  "features": ["<feature>", "..."],
  "keywords": ["<keyword>", "..."],
  "audience": ["<audience fit>", "..."],
  "pros": ["<review-derived pro>", "..."],
  "cons": ["<review-derived con>", "..."],
  "review_summary": "<1 sentence summary of overall sentiment>"
}}
""".strip()

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model=model_name, contents=prompt)
    data = _extract_json((resp.text or "").strip()) or {}
    return data

def compute_signature_for_profile(product: Dict[str, Any], reviews: List[Dict[str, Any]]) -> str:
    return _sig(product.get("name",""), product.get("category",""), float(product.get("price",0)), reviews)
