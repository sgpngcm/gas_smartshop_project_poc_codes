from typing import List, Dict, Any, Optional
import json
import re

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


def generate_user_insights_bullets(
    *,
    api_key: str,
    model_name: str,
    username: str,
    purchases: List[Dict[str, Any]],
    recs: List[Dict[str, Any]],
) -> List[str]:
    """
    Returns readable bullet points as list[str].
    Uses google.genai (new SDK).
    """
    if not api_key:
        return ["AI Insights unavailable: missing GEMINI_API_KEY."]

    # Keep prompt small for speed
    purchases_small = purchases[:10]
    recs_small = recs[:4]

    prompt = f"""
You are SmartShop's shopping analyst.

User: {username}

Purchase history JSON:
{json.dumps(purchases_small, ensure_ascii=False)}

Recommendations JSON:
{json.dumps(recs_small, ensure_ascii=False)}

Return ONLY valid JSON in this exact schema:
{{
  "bullets": [
    "string",
    "string",
    "string",
    "string",
    "string"
  ]
}}

Rules:
- 5 to 7 bullets total.
- Each bullet <= 18 words.
- Do NOT invent products not in the JSON.
- Make it easy to read.
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = (resp.text or "").strip()
    except Exception as e:
        # return a single bullet with error type (safe)
        return [f"AI Insights temporarily unavailable. ({type(e).__name__})"]

    data = _extract_json_object(text)
    bullets = (data or {}).get("bullets", [])

    if isinstance(bullets, list) and bullets:
        cleaned = []
        for b in bullets:
            s = str(b).strip().lstrip("•- ").strip()
            if s:
                cleaned.append(s)
        return cleaned[:7] if cleaned else ["No insights generated."]

    # Fallback if model didn't return JSON
    if text:
        lines = [ln.strip().lstrip("•- ").strip() for ln in text.splitlines() if ln.strip()]
        return lines[:7] if lines else ["No insights generated."]
    return ["No insights generated."]
