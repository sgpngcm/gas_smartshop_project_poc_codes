# backend/smartshop/views.py

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.cache import cache

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import SmartShopProduct, SmartShopPurchaseOrder, UserAIInsight, ProductReview, ProductAIReviewDigest
from .serializers import RegisterSerializer, PurchaseSerializer, ProductSerializer, ProductReviewSerializer
from .reco_service import get_recommendations_for_user
from .ai_insights import generate_user_insights_bullets
from .utils import purchase_signature, reviews_signature

from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .smart_reviews_ai import generate_product_review_digest
from .gemini_assistant import call_gemini_with_session_history

# Smart Search AI helpers (you already imported these earlier)
from .smart_search_ai import (
    gemini_parse_smart_search_v2,
    gemini_rerank_with_reasons,
    smart_search_cache_key,
)


# ----------------------------
# AUTH
# ----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response({"ok": True})
    return Response(s.errors, status=400)


# ----------------------------
# STORE
# ----------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def products_list(request):
    qs = SmartShopProduct.objects.select_related("ai_profile").all().order_by("-id")
    data = ProductSerializer(qs, many=True).data
    return Response(data)


# ----------------------------
# PURCHASES
# ----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_purchases(request):
    qs = (
        SmartShopPurchaseOrder.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-purchase_date")
    )
    data = PurchaseSerializer(qs, many=True).data
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def buy_product(request):
    product_id = request.data.get("product_id")
    qty = int(request.data.get("quantity") or 1)

    try:
        product = SmartShopProduct.objects.get(id=product_id)
    except SmartShopProduct.DoesNotExist:
        return Response({"detail": "Product not found."}, status=404)

    po = SmartShopPurchaseOrder.objects.create(
        user=request.user,
        product=product,
        quantity=max(1, qty),
    )
    return Response({"ok": True, "purchase_id": po.id})


# ----------------------------
# AI: RECOMMENDATIONS
# ----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendations(request):
    force = request.query_params.get("force") == "1"
    data = get_recommendations_for_user(request.user, max_items=4, force=force)
    return Response(data)


# ----------------------------
# AI: INSIGHTS (cached)
# ----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_insights(request):
    user = request.user

    purchases_qs = (
        SmartShopPurchaseOrder.objects
        .filter(user=user)
        .select_related("product")
        .order_by("-purchase_date")[:15]
    )

    purchases_compact = [
        {"name": p.product.name, "category": p.product.category, "price": float(p.product.price), "qty": p.quantity}
        for p in purchases_qs
    ]

    sig = purchase_signature(purchases_compact)
    force = request.query_params.get("force") == "1"

    cached = UserAIInsight.objects.filter(user=user).first()
    if (not force) and cached and cached.purchase_signature == sig and cached.bullets_json:
        return Response({
            "cached": True,
            "signature": sig,
            "bullets": cached.bullets_json,
            "text": cached.text,
            "updated_at": cached.updated_at,
        })

    # recommendations list (fast)
    rec_data = get_recommendations_for_user(user, max_items=4, force=False)
    recs = rec_data.get("recommended", [])

    bullets = generate_user_insights_bullets(
        api_key=getattr(settings, "GEMINI_API_KEY", None),
        model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
        username=user.username,
        purchases=purchases_compact,
        recs=recs,
    )

    if not cached:
        cached = UserAIInsight(user=user)

    cached.purchase_signature = sig
    cached.bullets_json = bullets
    cached.text = "\n".join([f"• {b}" for b in bullets])
    cached.save()

    return Response({
        "cached": False,
        "signature": sig,
        "bullets": bullets,
        "text": cached.text,
        "updated_at": cached.updated_at,
    })


# ----------------------------
# AI: SMART SEARCH (Step C2 applied here)
# ----------------------------
@api_view(["GET"])
@permission_classes([AllowAny])  # switch to IsAuthenticated if you want login-only
def smart_search(request):
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response({"interpreted_query": None, "results": [], "cached": False})

    limit = int(request.query_params.get("limit") or 24)
    limit = max(1, min(limit, 50))

    # categories available in DB
    categories = list(SmartShopProduct.objects.values_list("category", flat=True).distinct())

    parsed = gemini_parse_smart_search_v2(
        api_key=getattr(settings, "GEMINI_API_KEY", None),
        model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
        user_query=q,
        categories=categories,
    )

    # Cache whole search response for identical query+parsed constraints
    key = smart_search_cache_key(q, parsed)
    cached_payload = cache.get(key)
    if cached_payload:
        return Response({**cached_payload, "cached": True})

    qs = SmartShopProduct.objects.select_related("ai_profile").all()


    # Apply category filter (if any)
    if parsed.get("categories"):
        qs = qs.filter(category__in=parsed["categories"])

    # Apply price filters
    if parsed.get("price_min") is not None:
        qs = qs.filter(price__gte=parsed["price_min"])
    if parsed.get("price_max") is not None:
        qs = qs.filter(price__lte=parsed["price_max"])

    # Keyword matching (name + category) using parsed tokens
    tokens = []
    for t in (parsed.get("must_include") or []) + (parsed.get("keywords") or []) + (parsed.get("use_cases") or []) + (parsed.get("audience") or []):
        t = str(t).strip().lower()
        if t and t not in tokens:
            tokens.append(t)

    exclude_tokens = parsed.get("exclude") or []

    if tokens:
        cond = Q()
        for t in tokens:
            cond |= Q(name__icontains=t) | Q(category__icontains=t)
        qs = qs.filter(cond)

    for t in exclude_tokens:
        t = str(t).strip().lower()
        if t:
            qs = qs.exclude(Q(name__icontains=t) | Q(category__icontains=t))

    # Ordering for candidate pool (keep stable)
    if parsed.get("sort") == "price_asc":
        qs = qs.order_by("price")
    elif parsed.get("sort") == "price_desc":
        qs = qs.order_by("-price")
    elif parsed.get("sort") == "newest":
        qs = qs.order_by("-id")
    else:
        qs = qs.order_by("-id")

    # Candidate pool (bigger than limit for reranking)
    candidates = list(qs[:60])

    # If nothing found, broaden (remove strict category filter)
    if not candidates:
        qs2 = SmartShopProduct.objects.select_related("ai_profile").all().order_by("-id")
        if parsed.get("price_max") is not None:
            qs2 = qs2.filter(price__lte=parsed["price_max"])
        candidates = list(qs2[:60])



    # Build compact candidate list for Gemini reranker (includes AI profile fields)
    cand_compact = []
    for p in candidates[:30]:
        prof = getattr(p, "ai_profile", None)
        cand_compact.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "ai_short_description": (getattr(prof, "short_description", "") or "").strip() if prof else "",
            "ai_review_summary": (getattr(prof, "review_summary", "") or "").strip() if prof else "",
        })

    ranked = []
    if parsed.get("intent") == "recommend":
        ranked = gemini_rerank_with_reasons(
            api_key=getattr(settings, "GEMINI_API_KEY", None),
            model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
            user_query=q,
            parsed=parsed,
            candidates=cand_compact,
            max_items=min(limit, 12),
        )

    # If rerank failed or intent is search, do simple relevance scoring
    if not ranked:
        def score(p: SmartShopProduct) -> int:
            text = f"{p.name} {p.category}".lower()
            s = 0
            for t in parsed.get("must_include", []):
                if t in text:
                    s += 6
            for t in parsed.get("keywords", []):
                if t in text:
                    s += 3
            for t in parsed.get("use_cases", []):
                if t in text:
                    s += 2
            if parsed.get("categories") and p.category in parsed["categories"]:
                s += 2
            return s

        sorted_candidates = candidates[:]
        if parsed.get("sort") == "relevance":
            sorted_candidates.sort(key=score, reverse=True)

        ranked = [{"id": p.id, "reason": ""} for p in sorted_candidates[: min(limit, 12)]]

    ranked_ids = [int(x["id"]) for x in ranked if isinstance(x, dict) and "id" in x]
    reason_by_id = {int(x["id"]): (x.get("reason") or "").strip() for x in ranked if isinstance(x, dict) and "id" in x}

    # Fetch final products (and their ai_profile if exists)
    prod_qs = SmartShopProduct.objects.filter(id__in=ranked_ids).select_related("ai_profile")
    prod_data = ProductSerializer(prod_qs, many=True).data
    by_id = {p["id"]: p for p in prod_data}

    results = []
    for pid in ranked_ids:
        p = by_id.get(pid)
        if not p:
            continue

        # -----------------------------
        # Step C2: More specific explanation (profile+review-based)
        # -----------------------------
        reason = reason_by_id.get(pid)

        # Prefer AI profile signals if serializer provides them
        ai_use_cases = p.get("ai_use_cases") or []
        ai_features = p.get("ai_features") or []
        ai_review_summary = (p.get("ai_review_summary") or "").strip()
        ai_short_desc = (p.get("ai_short_description") or "").strip()

        if not reason:
            parts = []

            # Tie to user use case first
            if parsed.get("use_cases"):
                parts.append(f"Good for {parsed['use_cases'][0]}")

            # Use product profile use case/features if available
            if ai_use_cases:
                parts.append(f"Matches use case: {ai_use_cases[0]}")
            if ai_features:
                parts.append(f"Feature: {ai_features[0]}")

            # Budget/audience context
            if parsed.get("audience"):
                parts.append(f"Fits {parsed['audience'][0]}")
            if parsed.get("price_max") is not None:
                parts.append(f"Within budget (≤ ${int(parsed['price_max'])})")

            # Add review sentiment (grounded)
            if ai_review_summary:
                parts.append(ai_review_summary)

            # Final fallback if still empty
            if not parts and ai_short_desc:
                parts.append(ai_short_desc)

            reason = " • ".join(parts) if parts else "Matched your search intent and keywords."

        # IMPORTANT: your frontend currently reads p.match_summary
        p["match_summary"] = reason
        results.append(p)

        if len(results) >= limit:
            break

    payload = {
        "interpreted_query": parsed,
        "results": results,
        "cached": False,
    }

    cache.set(key, payload, timeout=600)
    return Response(payload)

def _user_purchased_product(user, product_id: int) -> bool:
    return SmartShopPurchaseOrder.objects.filter(user=user, product_id=product_id).exists()


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request, product_id: int):
    """
    Returns product + avg rating + reviews + AI digest (cached).
    """
    # Load product (include ai_profile if you have it)
    qs = SmartShopProduct.objects.select_related("ai_profile").filter(id=product_id)
    if not qs.exists():
        return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    # Annotate rating stats
    qs = qs.annotate(
        avg_rating=Avg("reviews__rating"),
        ratings_count=Count("reviews__id"),
    ).prefetch_related("reviews__user")

    product = qs.first()

    # Serialize product (includes reviews list)
    data = ProductSerializer(product).data
    data["avg_rating"] = float(data["avg_rating"] or 0.0)
    data["ratings_count"] = int(data["ratings_count"] or 0)

    # Build compact reviews for signature + AI generation
    reviews_qs = ProductReview.objects.filter(product_id=product_id).select_related("user").order_by("-updated_at")[:30]
    reviews_compact = [
        {"rating": r.rating, "title": r.title, "body": r.body}
        for r in reviews_qs
    ]
    sig = reviews_signature(reviews_compact)

    # Fetch or update AI digest cache
    digest = ProductAIReviewDigest.objects.filter(product_id=product_id).first()
    if digest and digest.reviews_signature == sig:
        ai_digest = {
            "cached": True,
            "highlights": digest.highlights_json,
            "sample_reviews": digest.sample_reviews_json,
            "updated_at": digest.updated_at,
            "label": "AI-generated highlights & sample reviews (not real user reviews).",
        }
    else:
        # Generate (only if we have Gemini key)
        product_for_ai = {
            "name": product.name,
            "category": product.category,
            "price": float(product.price),
            "ai_short_description": (getattr(getattr(product, "ai_profile", None), "short_description", "") or "").strip(),
            "ai_review_summary": (getattr(getattr(product, "ai_profile", None), "review_summary", "") or "").strip(),
        }

        ai = generate_product_review_digest(
            api_key=getattr(settings, "GEMINI_API_KEY", None),
            model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
            product=product_for_ai,
            reviews=reviews_compact,
        )

        if not digest:
            digest = ProductAIReviewDigest(product_id=product_id)

        digest.reviews_signature = sig
        digest.highlights_json = ai.get("highlights", []) or []
        digest.sample_reviews_json = ai.get("sample_reviews", []) or []
        digest.save()

        ai_digest = {
            "cached": False,
            "highlights": digest.highlights_json,
            "sample_reviews": digest.sample_reviews_json,
            "updated_at": digest.updated_at,
            "label": "AI-generated highlights & sample reviews (not real user reviews).",
        }

    # Can current user review?
    can_review = False
    if request.user and request.user.is_authenticated:
        can_review = _user_purchased_product(request.user, product_id)

    data["ai_review_digest"] = ai_digest
    data["can_review"] = can_review

    # Return also user's own review (if any) for convenience
    if request.user and request.user.is_authenticated:
        mine = ProductReview.objects.filter(product_id=product_id, user=request.user).first()
        data["my_review"] = ProductReviewSerializer(mine).data if mine else None
    else:
        data["my_review"] = None

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upsert_product_review(request, product_id: int):
    """
    Create or update a review (rating + optional title/body).
    Only allowed if user has purchased the product.
    """
    if not _user_purchased_product(request.user, product_id):
        return Response(
            {"detail": "You can only review items you have purchased."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Validate product exists
    if not SmartShopProduct.objects.filter(id=product_id).exists():
        return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    rating = request.data.get("rating", 5)
    title = (request.data.get("title") or "").strip()
    body = (request.data.get("body") or "").strip()

    try:
        rating = int(rating)
    except Exception:
        rating = 5
    rating = max(1, min(rating, 5))

    review, _created = ProductReview.objects.get_or_create(
        product_id=product_id,
        user=request.user,
        defaults={"rating": rating, "title": title, "body": body},
    )
    if not _created:
        review.rating = rating
        review.title = title
        review.body = body
        review.save()

    return Response(ProductReviewSerializer(review).data, status=status.HTTP_200_OK)

# ----------------------------
# VIRTUAL SHOPPING ASSISTANT (Gemini + session history)
# ----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])  # switch to IsAuthenticated if you want
def assistant_chat(request):
    """
    POST { "message": "..." }
    Stores chat history in Django session:
      request.session["assistant_history"] = [{"role":"user|assistant","content":"..."}]
    """
    msg = (request.data.get("message") or "").strip()
    if not msg:
        return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    history = request.session.get("assistant_history", [])
    if not isinstance(history, list):
        history = []

    # Append user message
    history.append({"role": "user", "content": msg})

    # Call Gemini
    reply = call_gemini_with_session_history(history, msg)

    # Append assistant reply
    history.append({"role": "assistant", "content": reply})

    # Trim history
    history = history[-30:]
    request.session["assistant_history"] = history
    request.session.modified = True

    return Response({"reply": reply, "history": history})


@api_view(["POST"])
@permission_classes([AllowAny])
def assistant_reset(request):
    request.session["assistant_history"] = []
    request.session.modified = True
    return Response({"ok": True})


