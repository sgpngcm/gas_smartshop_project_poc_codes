from typing import Dict, Any, List
from django.conf import settings
from django.db.models import Count

from .models import SmartShopProduct, SmartShopPurchaseOrder, UserRecommendationCache
from .serializers import ProductSerializer
from .utils import purchase_signature
from .gemini_client import gemini_recommend_products_with_reasons
from .also_bought import also_bought_for_user


def _fallback_recommendations_for_user(user, max_items: int = 4) -> List[SmartShopProduct]:
    """
    Simple non-AI fallback:
    - If user has categories purchased, recommend similar categories first (cheaper first).
    - Else recommend cheapest items not yet purchased.
    """
    purchased_ids = set(
        SmartShopPurchaseOrder.objects.filter(user=user).values_list("product_id", flat=True)
    )
    purchased_categories = list(
        SmartShopPurchaseOrder.objects.filter(user=user).values_list("product__category", flat=True)
    )

    qs = SmartShopProduct.objects.exclude(id__in=purchased_ids)
    products = list(qs)

    if purchased_categories:
        products.sort(key=lambda p: (p.category not in purchased_categories, float(p.price)))
        return products[:max_items]

    return list(qs.order_by("price")[:max_items])


def _attach_social_proof(user, recommended_products: List[Dict[str, Any]], top_n: int = 4):
    """
    Adds:
      - also_bought_count per recommended product
      - also_bought list for the response payload
    """
    also = also_bought_for_user(user, top_n=top_n)
    also_counts = {int(x["product_id"]): int(x["count"]) for x in also}

    for p in recommended_products:
        pid = int(p.get("id"))
        p["also_bought_count"] = int(also_counts.get(pid, 0))

    return also


def _social_proof_context(user, top_n: int = 6) -> Dict[str, Any]:
    """
    Returns small 'social proof' context for Gemini prompt:
    - also_bought list with names/categories
    - top categories among similar shoppers
    """
    # 1) Also-bought product ids + counts
    also = also_bought_for_user(user, top_n=top_n)
    also_ids = [int(x["product_id"]) for x in also]

    products = SmartShopProduct.objects.filter(id__in=also_ids)
    by_id = {p.id: p for p in products}

    also_named = []
    for row in also:
        pid = int(row["product_id"])
        p = by_id.get(pid)
        if not p:
            continue
        also_named.append({
            "id": pid,
            "name": p.name,
            "category": p.category,
            "count": int(row["count"]),
        })

    # 2) Find similar shoppers and their top categories (lightweight)
    user_product_ids = list(
        SmartShopPurchaseOrder.objects.filter(user=user).values_list("product_id", flat=True)
    )
    if not user_product_ids:
        return {"also_bought_named": also_named, "top_categories_among_similar": []}

    similar_user_ids = (
        SmartShopPurchaseOrder.objects
        .filter(product_id__in=user_product_ids)
        .exclude(user=user)
        .values_list("user_id", flat=True)
        .distinct()
    )

    top_cat_rows = (
        SmartShopPurchaseOrder.objects
        .filter(user_id__in=similar_user_ids)
        .values("product__category")
        .annotate(c=Count("product__category"))
        .order_by("-c")[:3]
    )

    top_categories = [
        {"category": row["product__category"], "count": int(row["c"])}
        for row in top_cat_rows
        if row.get("product__category")
    ]

    return {
        "also_bought_named": also_named,
        "top_categories_among_similar": top_categories,
    }


def get_recommendations_for_user(user, max_items: int = 4, force: bool = False) -> Dict[str, Any]:
    """
    Returns:
    {
      "cached": bool,
      "signature": "...",
      "purchase_count": n,
      "recommended": [{...product fields..., "reason": "...", "also_bought_count": int}],
      "also_bought": [{"product_id": int, "count": int}, ...],
      "updated_at": "...",
    }
    """
    purchased_qs = (
        SmartShopPurchaseOrder.objects
        .filter(user=user)
        .select_related("product")
        .order_by("-purchase_date")
    )
    purchase_count = purchased_qs.count()

    purchases_compact = [
        {
            "name": po.product.name,
            "category": po.product.category,
            "price": float(po.product.price),
            "qty": po.quantity,
        }
        for po in purchased_qs[:15]
    ]
    sig = purchase_signature(purchases_compact)

    # -----------------------------
    # Cache hit
    # -----------------------------
    cache = UserRecommendationCache.objects.filter(user=user).first()
    if (not force) and cache and cache.purchase_signature == sig and cache.items_json:
        ids = []
        id_to_reason = {}
        for item in cache.items_json:
            if isinstance(item, dict) and "id" in item:
                try:
                    pid = int(item["id"])
                    ids.append(pid)
                    id_to_reason[pid] = (item.get("reason") or "").strip()
                except Exception:
                    continue

        qs = SmartShopProduct.objects.filter(id__in=ids)
        products = ProductSerializer(qs, many=True).data
        products_by_id = {p["id"]: p for p in products}

        ordered: List[Dict[str, Any]] = []
        for pid in ids:
            p = products_by_id.get(pid)
            if p:
                p["reason"] = id_to_reason.get(pid) or "Recommended based on your shopping patterns."
                ordered.append(p)

        also = _attach_social_proof(user, ordered, top_n=max_items)

        return {
            "cached": True,
            "signature": sig,
            "purchase_count": purchase_count,
            "recommended": ordered,
            "also_bought": also,
            "updated_at": cache.updated_at,
        }

    # -----------------------------
    # Build prompt inputs for Gemini
    # -----------------------------
    catalog_qs = SmartShopProduct.objects.all()
    catalog_for_prompt = [
        {"id": p.id, "name": p.name, "category": p.category, "price": float(p.price)}
        for p in catalog_qs
    ]

    purchased_for_prompt = [
        {
            "id": po.product.id,
            "name": po.product.name,
            "category": po.product.category,
            "price": float(po.product.price),
        }
        for po in purchased_qs[:20]
    ]

    purchased_ids = set(purchased_qs.values_list("product_id", flat=True))

    # -----------------------------
    # Social proof context for Gemini (compact)
    # -----------------------------
    sp = _social_proof_context(user, top_n=6)

    # Keep the prompt small: only include top 5 also-bought items
    social_proof_context = {
        "also_bought_top": sp.get("also_bought_named", [])[:5],
        "top_categories_among_similar": sp.get("top_categories_among_similar", [])[:3],
        "note": "Use these only as supporting signals; never invent purchases.",
    }

    # -----------------------------
    # Gemini recommendations with reasons (with social proof)
    # -----------------------------
    items: List[Dict[str, Any]] = []
    try:
        items = gemini_recommend_products_with_reasons(
            api_key=getattr(settings, "GEMINI_API_KEY", None),
            model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
            purchased=purchased_for_prompt,
            catalog=catalog_for_prompt,
            max_items=max_items,
            # ✅ NEW: pass social proof context
            social_proof=social_proof_context,
        )
    except TypeError:
        # If your gemini_client does not yet accept social_proof, fall back safely
        items = gemini_recommend_products_with_reasons(
            api_key=getattr(settings, "GEMINI_API_KEY", None),
            model_name=getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash"),
            purchased=purchased_for_prompt,
            catalog=catalog_for_prompt,
            max_items=max_items,
        )
    except Exception:
        items = []

    # Filter out already purchased
    items = [
        x for x in items
        if isinstance(x, dict)
        and "id" in x
        and (int(x["id"]) not in purchased_ids)
    ]

    # -----------------------------
    # Fallback (if Gemini fails/empty)
    # -----------------------------
    if not items:
        fallback_products = _fallback_recommendations_for_user(user, max_items=max_items)
        items = [{"id": p.id, "reason": "Recommended based on similar categories you’ve purchased."} for p in fallback_products]

    # Load product details in correct order
    ids = []
    id_to_reason = {}
    for it in items:
        try:
            pid = int(it.get("id"))
            ids.append(pid)
            id_to_reason[pid] = (it.get("reason") or "").strip()
        except Exception:
            continue

    qs = SmartShopProduct.objects.filter(id__in=ids)
    products = ProductSerializer(qs, many=True).data
    products_by_id = {p["id"]: p for p in products}

    ordered: List[Dict[str, Any]] = []
    for pid in ids:
        p = products_by_id.get(pid)
        if p:
            p["reason"] = id_to_reason.get(pid) or "Recommended based on your shopping patterns."
            ordered.append(p)

    # Attach also-bought signals to response
    also = _attach_social_proof(user, ordered, top_n=max_items)

    # -----------------------------
    # Save/update cache
    # -----------------------------
    if not cache:
        cache = UserRecommendationCache(user=user)

    cache.purchase_signature = sig
    cache.items_json = [{"id": p["id"], "reason": p.get("reason", "")} for p in ordered]
    cache.save()

    return {
        "cached": False,
        "signature": sig,
        "purchase_count": purchase_count,
        "recommended": ordered,
        "also_bought": also,
        "updated_at": cache.updated_at,
    }
