from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class SmartShopProduct(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.category})"


class SmartShopPurchaseOrder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(SmartShopProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"User {self.user_id} purchased {self.product_id} x{self.quantity}"


class UserAIInsight(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_insight")
    purchase_signature = models.CharField(max_length=64)  # sha256 hex
    bullets_json = models.JSONField(default=list)         # list[str]
    text = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AIInsight(user={self.user.username}, updated={self.updated_at})"


class UserRecommendationCache(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_recommendations")
    purchase_signature = models.CharField(max_length=64)
    items_json = models.JSONField(default=list)  # [{id, reason}, ...]
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"UserRecommendationCache(user={self.user.username}, updated={self.updated_at})"


class ProductAIProfile(models.Model):
    product = models.OneToOneField("SmartShopProduct", on_delete=models.CASCADE, related_name="ai_profile")
    source_signature = models.CharField(max_length=64, db_index=True, default="")

    short_description = models.TextField(blank=True, default="")
    use_cases = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    audience = models.JSONField(default=list, blank=True)
    pros = models.JSONField(default=list, blank=True)
    cons = models.JSONField(default=list, blank=True)
    review_summary = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AIProfile({self.product_id})"


class ProductReview(models.Model):
    """
    One review per (user, product).
    Rating is 1..5.
    Only purchasers are allowed to create/update (enforced in views).
    """
    product = models.ForeignKey("SmartShopProduct", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
        null=False,
        blank=False,
    )

    
    
    rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "user")
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.product_id} by {self.user_id} ({self.rating})"


class ProductAIReviewDigest(models.Model):
    """
    Cached AI content derived from (real) reviews + product AI fields.
    This is NOT presented as real user reviews. We label it clearly in response.
    """
    product = models.OneToOneField("SmartShopProduct", on_delete=models.CASCADE, related_name="ai_review_digest")
    reviews_signature = models.CharField(max_length=64, default="", db_index=True)

    highlights_json = models.JSONField(default=list, blank=True)
    sample_reviews_json = models.JSONField(default=list, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI digest for product {self.product_id}"
