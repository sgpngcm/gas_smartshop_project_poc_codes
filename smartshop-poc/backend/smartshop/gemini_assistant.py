from __future__ import annotations

import json
from typing import Any, Dict, List

from django.conf import settings
from django.core.cache import cache

from google import genai

from .models import SmartShopProduct


def _inventory_digest() -> str:
    """
    Compact inventory context for the assistant.
    Cached for speed.
    """
    cache_key = "smartshop_inventory_digest_v1"
    cached = cache.get(cache_key)
    if cached:
        return cached

    qs = (
        SmartShopProduct.objects
        .select_related("ai_profile")
        .all()
        .order_by("-id")[:120]
    )

    items: List[Dict[str, Any]] = []
    for p in qs:
        prof = getattr(p, "ai_profile", None)
        items.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            # If these exist in your ProductAIProfile, they help grounding:
            "ai_short_description": (getattr(prof, "short_description", "") or "").strip() if prof else "",
            "ai_review_summary": (getattr(prof, "review_summary", "") or "").strip() if prof else "",
        })

    digest = json.dumps({"inventory": items}, ensure_ascii=False)
    cache.set(cache_key, digest, timeout=300)  # 5 minutes
    return digest


def build_system_message() -> str:
    inventory_json = _inventory_digest()

    return f"""
You are SmartShop's Virtual Shopping Assistant.

GOALS
- Help users find products, compare options, and decide what to buy.
- Ask 1–2 clarifying questions if the request is vague (budget/use-case/constraints).
- Recommend up to 5 products max.

STRICT RULES
- Only recommend products that exist in the inventory context below.
- Never invent products, prices, categories, features, or reviews.
- If you cannot find a match, say so and ask a clarifying question.

RESPONSE FORMAT
- Start with a short helpful reply.
- Then list recommendations as bullets:
  - Product Name (Category) — $Price — Reason (<= 18 words, grounded in context)

INVENTORY CONTEXT (JSON)
{inventory_json}
""".strip()


def call_gemini_with_session_history(history: List[dict], user_message: str) -> str:
    """
    Uses Gemini generate_content. We inject the System Message + transcript.
    Session history is text-transcript based (simple and reliable for POC).
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    model_name = getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash")

    if not api_key:
        return "Gemini API key is not configured on the server."

    # Build transcript from last N messages
    transcript_lines: List[str] = []
    for m in history[-20:]:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        prefix = "USER" if role == "user" else "ASSISTANT"
        transcript_lines.append(f"{prefix}: {content}")

    transcript_lines.append(f"USER: {user_message}")
    transcript = "\n".join(transcript_lines)

    prompt = f"""
SYSTEM:
{build_system_message()}

CONVERSATION SO FAR:
{transcript}

ASSISTANT:
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = (resp.text or "").strip()
        return text or "Sorry, I couldn't generate a reply."
    except Exception as e:
        return f"Assistant error: {str(e)}"
