import random
from django.core.management.base import BaseCommand
from smartshop.models import SmartShopProduct, ProductReview

TEMPLATES = [
    ("Good value", "Works well for the price. Solid quality."),
    ("Lightweight", "Easy to carry and does the job."),
    ("Student friendly", "Affordable and useful for daily use."),
    ("Reliable", "No issues so far. Would buy again."),
    ("Nice design", "Looks good and feels sturdy."),
    ("Okay", "Decent, but could be improved."),
    ("Convenient", "Very handy for my needs."),
]

CONS = [
    ("Minor drawback", "Wish the build was a bit sturdier."),
    ("Size", "Smaller than expected."),
    ("Packaging", "Packaging could be better."),
    ("Learning curve", "Took some time to get used to."),
]

class Command(BaseCommand):
    help = "Seed simple buyer reviews for products (helps AI profiles)."

    def add_arguments(self, parser):
        parser.add_argument("--per", type=int, default=3, help="Reviews per product (default 3)")
        parser.add_argument("--max-products", type=int, default=80, help="Max products to add reviews for")

    def handle(self, *args, **opts):
        per = max(1, min(int(opts["per"]), 10))
        max_products = max(1, int(opts["max_products"]))

        products = list(SmartShopProduct.objects.all().order_by("-id")[:max_products])
        created = 0

        for p in products:
            existing = ProductReview.objects.filter(product=p).count()
            if existing >= per:
                continue

            need = per - existing
            for _ in range(need):
                if random.random() < 0.75:
                    title, body = random.choice(TEMPLATES)
                    rating = random.choice([4, 5, 5, 4])
                else:
                    title, body = random.choice(CONS)
                    rating = random.choice([3, 3, 2])

                ProductReview.objects.create(
                    product=p,
                    rating=rating,
                    title=title,
                    body=body
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {created} reviews."))
