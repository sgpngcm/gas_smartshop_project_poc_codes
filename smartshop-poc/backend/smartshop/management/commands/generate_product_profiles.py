from django.conf import settings
from django.core.management.base import BaseCommand
from smartshop.models import SmartShopProduct, ProductReview, ProductAIProfile
from smartshop.product_profile_ai import generate_product_profile, compute_signature_for_profile

class Command(BaseCommand):
    help = "Generate/refresh AI profiles for products using Gemini (cached in DB)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=120)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **opts):
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        model_name = getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash")

        limit = max(1, int(opts["limit"]))
        force = bool(opts["force"])

        qs = SmartShopProduct.objects.all().order_by("-id")[:limit]
        updated = 0
        skipped = 0

        for p in qs:
            reviews = list(
                ProductReview.objects.filter(product=p)
                .order_by("-created_at")
                .values("rating", "title", "body")[:8]
            )

            product_payload = {"id": p.id, "name": p.name, "category": p.category, "price": float(p.price)}
            sig = compute_signature_for_profile(product_payload, reviews)

            prof = ProductAIProfile.objects.filter(product=p).first()
            if prof and prof.source_signature == sig and not force:
                skipped += 1
                continue

            data = generate_product_profile(
                api_key=api_key,
                model_name=model_name,
                product=product_payload,
                reviews=reviews,
            ) or {}

            if not prof:
                prof = ProductAIProfile(product=p)

            prof.source_signature = sig
            prof.short_description = str(data.get("short_description", "")).strip()
            prof.use_cases = data.get("use_cases", []) or []
            prof.features = data.get("features", []) or []
            prof.keywords = data.get("keywords", []) or []
            prof.audience = data.get("audience", []) or []
            prof.pros = data.get("pros", []) or []
            prof.cons = data.get("cons", []) or []
            prof.review_summary = str(data.get("review_summary", "")).strip()
            prof.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Profiles updated: {updated}, skipped: {skipped}"))
