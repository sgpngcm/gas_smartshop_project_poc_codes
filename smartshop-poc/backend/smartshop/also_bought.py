from typing import Dict, List, Any
from django.db.models import Count

from .models import SmartShopPurchaseOrder


def also_bought_for_user(user, top_n: int = 4) -> List[Dict[str, Any]]:
    """
    Returns items users also bought, based on the user's purchased products.
    Output: [{"product_id": 12, "count": 5}, ...]
    """
    user_product_ids = list(
        SmartShopPurchaseOrder.objects.filter(user=user).values_list("product_id", flat=True)
    )
    if not user_product_ids:
        return []

    # Find other users who bought any of user's items
    other_user_ids = (
        SmartShopPurchaseOrder.objects
        .filter(product_id__in=user_product_ids)
        .exclude(user=user)
        .values_list("user_id", flat=True)
        .distinct()
    )

    if not other_user_ids:
        return []

    # Count what those users also bought (excluding user's already purchased)
    qs = (
        SmartShopPurchaseOrder.objects
        .filter(user_id__in=other_user_ids)
        .exclude(product_id__in=user_product_ids)
        .values("product_id")
        .annotate(count=Count("product_id"))
        .order_by("-count")[:top_n]
    )
    return [{"product_id": row["product_id"], "count": row["count"]} for row in qs]
