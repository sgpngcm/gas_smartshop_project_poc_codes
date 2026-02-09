import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify
from django.conf import settings
import os

from smartshop.models import SmartShopProduct, SmartShopPurchaseOrder


PRODUCTS_20 = [
    ("Eco Water Bottle", "Lifestyle", Decimal("12.90")),
    ("Wireless Earbuds", "Electronics", Decimal("39.90")),
    ("Gaming Mouse", "Electronics", Decimal("24.50")),
    ("Yoga Mat", "Fitness", Decimal("18.00")),
    ("Running Shoes", "Fitness", Decimal("59.00")),
    ("Smart Watch", "Electronics", Decimal("89.00")),
    ("Coffee Grinder", "Home", Decimal("28.00")),
    ("Air Fryer Liners", "Home", Decimal("7.90")),
    ("Skincare Serum", "Beauty", Decimal("29.90")),
    ("Sunscreen SPF50", "Beauty", Decimal("15.90")),
    ("Laptop Stand", "Office", Decimal("21.50")),
    ("Mechanical Keyboard", "Office", Decimal("49.90")),
    ("LED Desk Lamp", "Office", Decimal("19.90")),
    ("Pet Grooming Brush", "Pets", Decimal("9.90")),
    ("Cat Toy Set", "Pets", Decimal("8.50")),
    ("Travel Backpack", "Lifestyle", Decimal("35.00")),
    ("Stainless Lunch Box", "Lifestyle", Decimal("14.90")),
    ("Protein Shaker", "Fitness", Decimal("11.50")),
    ("HDMI Cable 2m", "Electronics", Decimal("6.90")),
    ("Non-stick Pan", "Home", Decimal("22.90")),
]


class Command(BaseCommand):
    help = "Seeds SmartShop with demo users and realistic overlapping purchases for 'also-bought' recommendations."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all products and purchases before seeding.")
        parser.add_argument("--images-dir", type=str, default="product_images", help="MEDIA_ROOT subfolder for images.")
        parser.add_argument("--password", type=str, default="abc123456", help="Password for created demo users.")

    @transaction.atomic
    def handle(self, *args, **options):
        reset = bool(options["reset"])
        images_subdir = (options["images_dir"] or "product_images").strip()
        password = options["password"]

        if reset:
            SmartShopPurchaseOrder.objects.all().delete()
            SmartShopProduct.objects.all().delete()
            self.stdout.write(self.style.WARNING("Reset: deleted all SmartShopProduct and SmartShopPurchaseOrder rows."))

        # Create products (upsert)
        abs_images_dir = os.path.join(settings.MEDIA_ROOT, images_subdir)
        os.makedirs(abs_images_dir, exist_ok=True)

        products = []
        for name, category, price in PRODUCTS_20:
            p, _ = SmartShopProduct.objects.get_or_create(
                name=name,
                defaults={"category": category, "price": price},
            )
            p.category = category
            p.price = price

            # Auto attach image if exists: MEDIA_ROOT/product_images/<slug>.png
            slug = slugify(name)
            rel_path = f"{images_subdir}/{slug}.png"
            abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
            if os.path.exists(abs_path):
                if not p.image or p.image.name != rel_path:
                    p.image.name = rel_path

            p.save()
            products.append(p)

        # Create demo users
        demo_usernames = ["alice", "bob", "carol", "david", "emma", "frank"]
        users = []
        for uname in demo_usernames:
            u = User.objects.filter(username=uname).first()
            if not u:
                u = User.objects.create_user(username=uname, email=f"{uname}@example.com", password=password)
                self.stdout.write(self.style.WARNING(f"Created user '{uname}' (password: {password})"))
            users.append(u)

        # Helper: create purchases without duplicates
        def add_purchases(user, prod_list):
            existing = set(SmartShopPurchaseOrder.objects.filter(user=user).values_list("product_id", flat=True))
            for p in prod_list:
                if p.id in existing:
                    continue
                SmartShopPurchaseOrder.objects.create(
                    user=user,
                    product=p,
                    quantity=random.randint(1, 3),
                )

        # Build category pools for realistic overlap
        by_cat = {}
        for p in products:
            by_cat.setdefault(p.category, []).append(p)

        electronics = by_cat.get("Electronics", [])
        office = by_cat.get("Office", [])
        fitness = by_cat.get("Fitness", [])
        home = by_cat.get("Home", [])
        lifestyle = by_cat.get("Lifestyle", [])
        beauty = by_cat.get("Beauty", [])
        pets = by_cat.get("Pets", [])

        # Shared “popular items” to create overlapping signals
        popular_bundle = []
        popular_bundle += random.sample(electronics, k=min(2, len(electronics)))
        popular_bundle += random.sample(office, k=min(1, len(office)))
        popular_bundle += random.sample(lifestyle, k=min(1, len(lifestyle)))

        # User profiles (overlapping but not identical)
        plan = {
            "alice":  (electronics, office, lifestyle),
            "bob":    (electronics, fitness, home),
            "carol":  (beauty, lifestyle, home),
            "david":  (office, electronics, home),
            "emma":   (fitness, lifestyle, beauty),
            "frank":  (pets, home, lifestyle),
        }

        # Apply purchases
        for u in users:
            pref1, pref2, pref3 = plan[u.username]
            picks = []

            # Everyone buys the shared popular bundle (creates “also bought” signal)
            picks += popular_bundle

            # Each user buys additional items from their preferences
            for pref in [pref1, pref2, pref3]:
                if pref:
                    picks += random.sample(pref, k=min(2, len(pref)))

            # Add a couple random cross-category items for realism
            picks += random.sample(products, k=2)

            add_purchases(u, picks)

        self.stdout.write(self.style.SUCCESS("Done seeding demo users + products + overlapping purchases."))
        self.stdout.write(self.style.SUCCESS("Try logging in as: alice/bob/carol/david/emma/frank"))
