from django.contrib.auth.models import User
from rest_framework import serializers
from .models import SmartShopProduct, SmartShopPurchaseOrder, ProductAIProfile,ProductReview
from django.db.models import Avg, Count

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )

class ProductReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ProductReview
        fields = ["id", "username", "rating", "title", "body", "created_at", "updated_at"]

class ProductSerializer(serializers.ModelSerializer):
    # Computed review stats
    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)

    # Reviews list (filled in detail endpoint)
    reviews = ProductReviewSerializer(many=True, read_only=True)

    # Optional AI fields if you have an ai_profile relation (safe if missing)
    ai_short_description = serializers.SerializerMethodField()
    ai_review_summary = serializers.SerializerMethodField()

    class Meta:
        model = SmartShopProduct
        fields = [
            "id", "name", "category", "price", "image",
            "avg_rating", "ratings_count",
            "ai_short_description", "ai_review_summary",
            "reviews",
        ]

    def get_ai_short_description(self, obj):
        prof = getattr(obj, "ai_profile", None)
        if not prof:
            return ""
        return (getattr(prof, "short_description", "") or "").strip()

    def get_ai_review_summary(self, obj):
        prof = getattr(obj, "ai_profile", None)
        if not prof:
            return ""
        return (getattr(prof, "review_summary", "") or "").strip()



class PurchaseSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SmartShopPurchaseOrder
        fields = ["id", "product", "product_id", "quantity", "purchase_date"]
