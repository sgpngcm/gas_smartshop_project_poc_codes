# backend/smartshop/management/commands/seed_smartshop.py

import os
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.utils.text import slugify

from smartshop.models import SmartShopProduct, SmartShopPurchaseOrder


class Command(BaseCommand):
    help = (
        "Seeds SmartShop with 10–20 products and purchase orders for a target user. "
        "If images exist in MEDIA_ROOT/product_images/<slug>.png, they will be attached automatically."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            type=int,
            default=15,
            help="Number of products to seed (forced to 10–20). Default: 15.",
        )
        parser.add_argument(
            "--purchases",
            type=int,
            default=5,
            help="Number of purchases to create for the target user. Default: 5.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="If provided, deletes existing SmartShop products and purchase orders first.",
        )
        parser.add_argument(
            "--images-dir",
            type=str,
            default="product_images",
            help="Folder under MEDIA_ROOT containing product images. Default: product_images",
        )
        parser.add_argument(
            "--username",
            type=str,
            default="demo_user1",
            help="Username to seed purchases for. If missing, it will be created. Default: demo_user1",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="abc123456",
            help="Password for created demo user (only used if user does not exist). Default: abc123456",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        product_count = max(10, min(20, int(options["products"])))
        purchase_count = max(1, int(options["purchases"]))
        reset = bool(options["reset"])
        images_subdir = str(options["images_dir"]).strip() or "product_images"
        username = str(options["username"]).strip() or "demo_user1"
        password = str(options["password"])

        # Ensure target user exists (by username, so it matches JWT login user)
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=password,
            )
            self.stdout.write(self.style.WARNING(
                f"Created user '{user.username}' (id={user.id}). "
                f"Password set to: {password}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Using existing user '{user.username}' (id={user.id})."
            ))

        if reset:
            SmartShopPurchaseOrder.objects.all().delete()
            SmartShopProduct.objects.all().delete()
            self.stdout.write(self.style.WARNING("Reset enabled: deleted ALL SmartShop products and purchase orders."))

        # 20 sample products (we will pick 10–20 from these)
        sample_products = [
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

        chosen = random.sample(sample_products, k=product_count)

        # Ensure images folder exists
        abs_images_dir = os.path.join(settings.MEDIA_ROOT, images_subdir)
        os.makedirs(abs_images_dir, exist_ok=True)

        created_count = 0
        attached_images = 0
        missing_images = 0

        # Seed / upsert products and attach images if present
        for name, category, price in chosen:
            obj, created = SmartShopProduct.objects.get_or_create(
                name=name,
                defaults={"category": category, "price": price},
            )

            if created:
                created_count += 1
            else:
                # Keep seeded values consistent on reruns
                obj.category = category
                obj.price = price
                obj.save(update_fields=["category", "price"])

            # Attach AI image if file exists: MEDIA_ROOT/<images_subdir>/<slug>.png
            slug = slugify(name)
            filename = f"{slug}.png"
            rel_path = f"{images_subdir}/{filename}"
            abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

            if os.path.exists(abs_path):
                if not obj.image or obj.image.name != rel_path:
                    obj.image.name = rel_path
                    obj.save(update_fields=["image"])
                    attached_images += 1
            else:
                missing_images += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded products: {SmartShopProduct.objects.count()} total "
            f"({created_count} created this run)."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Images: attached/updated {attached_images}. Missing images for {missing_images} product(s)."
        ))

        # Create purchases for the target user (avoid duplicates)
        all_products = list(SmartShopProduct.objects.all())
        already = set(
            SmartShopPurchaseOrder.objects.filter(user=user).values_list("product_id", flat=True)
        )
        available = [p for p in all_products if p.id not in already]

        if not available:
            self.stdout.write(self.style.WARNING(
                f"User '{user.username}' already purchased all available products. No new purchases created."
            ))
            return

        purchase_count = min(purchase_count, len(available))
        picked = random.sample(available, k=purchase_count)

        for p in picked:
            SmartShopPurchaseOrder.objects.create(
                user=user,
                product=p,
                quantity=random.randint(1, 3),
            )

        self.stdout.write(self.style.SUCCESS(
            f"Created {purchase_count} purchase order(s) for user '{user.username}' (id={user.id})."
        ))
        self.stdout.write(self.style.SUCCESS("Done. Refresh React UI / AI endpoints."))
