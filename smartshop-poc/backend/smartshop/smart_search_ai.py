import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from google import genai


# -----------------------------
# Helpers
# -----------------------------
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


def _limit_words(s: str, max_words: int = 18) -> str:
    s = (s or "").strip()
    if not s:
        return s
    words = s.split()
    if len(words) <= max_words:
        return s
    return " ".join(words[:max_words])


def smart_search_cache_key(user_query: str, parsed: Dict[str, Any]) -> str:
    """
    Stable cache key so identical query+constraints returns cached payload.
    """
    payload = {
        "q": (user_query or "").strip().lower(),
        "parsed": parsed or {},
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return "smartsearch:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


# -----------------------------
# Step 1: Parse user query into constraints
# -----------------------------
def gemini_parse_smart_search_v2(
    *,
    api_key: str,
    model_name: str,
    user_query: str,
    categories: List[str],
) -> Dict[str, Any]:
    """
    Parses natural language query into structured constraints.

    Returns a dict with keys:
      intent: "search" | "recommend"
      categories: [str]
      price_min: float | None
      price_max: float | None
      keywords: [str]
      use_cases: [str]
      audience: [str]
      must_include: [str]
      exclude: [str]
      sort: "relevance" | "price_asc" | "price_desc" | "newest"
    """
    # Safe defaults if no API key or parsing fails
    defaults: Dict[str, Any] = {
        "intent": "search",
        "categories": [],
        "price_min": None,
        "price_max": None,
        "keywords": [],
        "use_cases": [],
        "audience": [],
        "must_include": [],
        "exclude": [],
        "sort": "relevance",
    }

    q = (user_query or "").strip()
    if not q:
        return defaults

    if not api_key:
        # Simple heuristic fallback (no Gemini)
        defaults["keywords"] = [x for x in re.split(r"[\s,]+", q.lower()) if len(x) >= 3][:8]
        defaults["intent"] = "recommend" if "recommend" in q.lower() else "search"
        return defaults

    # Keep category list small
    categories_small = categories[:60]

    prompt = f"""
You are SmartShop's smart search query parser.

User query:
{q}

Available categories (choose ONLY from this list if category applies):
{json.dumps(categories_small, ensure_ascii=False)}

Task:
Convert the query into a structured JSON object used for search/recommendation.

Rules:
- DO NOT invent categories not in the list.
- If query implies "recommend for me", set intent="recommend". Otherwise "search".
- Detect budget like "under $30", "below 20", "cheap", "student" (set price_max reasonably if implied).
- Extract use case like "hiking", "study", "gaming", "travel", "office".
- Output MUST be valid JSON ONLY, no extra text.

Schema:
{{
  "intent": "search" | "recommend",
  "categories": ["<category>", "..."],
  "price_min": <number|null>,
  "price_max": <number|null>,
  "keywords": ["<keyword>", "..."],
  "use_cases": ["<use case>", "..."],
  "audience": ["<audience>", "..."],
  "must_include": ["<term>", "..."],
  "exclude": ["<term>", "..."],
  "sort": "relevance" | "price_asc" | "price_desc" | "newest"
}}
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model_name, contents=prompt)
        data = _extract_json_object((resp.text or "").strip())
    except Exception:
        return defaults

    if not isinstance(data, dict):
        return defaults

    # Normalize fields
    out = dict(defaults)
    out["intent"] = "recommend" if str(data.get("intent", "search")).lower() == "recommend" else "search"

    cats = data.get("categories", [])
    if isinstance(cats, list):
        # keep only valid categories
        valid_set = set(categories_small)
        out["categories"] = [c for c in cats if isinstance(c, str) and c in valid_set][:5]

    def _num_or_none(x):
        try:
            if x is None:
                return None
            return float(x)
        except Exception:
            return None

    out["price_min"] = _num_or_none(data.get("price_min"))
    out["price_max"] = _num_or_none(data.get("price_max"))

    for k in ["keywords", "use_cases", "audience", "must_include", "exclude"]:
        v = data.get(k, [])
        if isinstance(v, list):
            cleaned = []
            for t in v:
                t = str(t).strip()
                if t and t.lower() not in [x.lower() for x in cleaned]:
                    cleaned.append(t)
            out[k] = cleaned[:10]

    sort = str(data.get("sort", "relevance")).lower()
    if sort in ["relevance", "price_asc", "price_desc", "newest"]:
        out["sort"] = sort

    return out


# -----------------------------
# Step 2: Rerank candidates with grounded reasons (<= 18 words)
# -----------------------------
def gemini_rerank_with_reasons(
    *,
    api_key: str,
    model_name: str,
    user_query: str,
    parsed: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    """
    Reranks candidates and returns short GROUNDED reasons (<= 18 words).
    Candidates SHOULD include:
      - id, name, category, price
      - ai_short_description (recommended)
      - ai_review_summary (recommended)

    Returns:
      [{"id": <int>, "reason": "<=18 words>"} ...]
    """
    if not api_key or not candidates:
        return []

    # Keep prompt small
    cand_small = candidates[: min(len(candidates), 30)]

    cand_for_prompt = []
    for c in cand_small:
        cand_for_prompt.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "category": c.get("category"),
            "price": c.get("price"),
            "ai_short_description": (c.get("ai_short_description") or "").strip(),
            "ai_review_summary": (c.get("ai_review_summary") or "").strip(),
        })

    parsed_min = {
        "intent": parsed.get("intent"),
        "categories": parsed.get("categories") or [],
        "price_min": parsed.get("price_min"),
        "price_max": parsed.get("price_max"),
        "use_cases": parsed.get("use_cases") or [],
        "audience": parsed.get("audience") or [],
        "must_include": parsed.get("must_include") or [],
        "exclude": parsed.get("exclude") or [],
    }

    prompt = f"""
You are SmartShop's smart search reranker.

USER QUERY:
{user_query}

INTERPRETED CONSTRAINTS:
{json.dumps(parsed_min, ensure_ascii=False)}

CANDIDATE PRODUCTS (choose ONLY from these):
{json.dumps(cand_for_prompt, ensure_ascii=False)}

Task:
Return the best {max_items} products in ranked order.

Reason rules (STRICT):
- Each reason MUST be grounded ONLY in provided fields:
  name, category, price, ai_short_description, ai_review_summary, and interpreted constraints.
- Each reason MUST be <= 18 words.
- Avoid generic phrasing ("based on your intent", "great choice", "recommended for you").
- Prefer: use case + feature/benefit + review sentiment + budget fit (if applicable).

Output JSON ONLY (no extra text):
{{
  "ranked": [
    {{"id": 123, "reason": "..." }},
    {{"id": 456, "reason": "..." }}
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
    if not data or "ranked" not in data:
        return []

    items = data.get("ranked")
    if not isinstance(items, list):
        return []

    valid_ids = {int(c.get("id")) for c in cand_small if c.get("id") is not None}

    out: List[Dict[str, Any]] = []
    seen = set()

    for it in items:
        if not isinstance(it, dict):
            continue
        pid = it.get("id")
        reason = it.get("reason", "")

        try:
            pid_int = int(pid)
        except (TypeError, ValueError):
            continue

        if pid_int not in valid_ids or pid_int in seen:
            continue

        reason_str = str(reason).strip()
        if not reason_str:
            reason_str = "Matches your needs and budget."

        reason_str = _limit_words(reason_str, 18)

        out.append({"id": pid_int, "reason": reason_str})
        seen.add(pid_int)

        if len(out) >= max_items:
            break

    return out
