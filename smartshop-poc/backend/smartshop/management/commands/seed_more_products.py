from __future__ import annotations

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from smartshop.models import SmartShopProduct


EXTRA_PRODUCTS_40 = [
    # Hiking / Outdoors
    {"name": "Compact Hiking Backpack 20L", "category": "Outdoors", "price": "29.90", "image": "products/compact_hiking_backpack_20l.png"},
    {"name": "Stainless Steel Water Bottle 750ml", "category": "Outdoors", "price": "12.90", "image": "products/stainless_steel_water_bottle_750ml.png"},
    {"name": "Lightweight Rain Poncho", "category": "Outdoors", "price": "8.90", "image": "products/lightweight_rain_poncho.png"},
    {"name": "Portable Camping Lantern LED", "category": "Outdoors", "price": "14.90", "image": "products/portable_camping_lantern_led.png"},
    {"name": "Trekking Poles Pair", "category": "Outdoors", "price": "24.90", "image": "products/trekking_poles_pair.png"},
    {"name": "Emergency Whistle + Compass", "category": "Outdoors", "price": "6.90", "image": "products/emergency_whistle_compass.png"},
    {"name": "Mini First Aid Kit Travel", "category": "Outdoors", "price": "9.90", "image": "products/mini_first_aid_kit_travel.png"},
    {"name": "Quick-Dry Microfiber Towel", "category": "Outdoors", "price": "7.90", "image": "products/quick_dry_microfiber_towel.png"},

    # Tech / Accessories
    {"name": "USB-C to USB-A Adapter", "category": "Electronics", "price": "4.90", "image": "products/usbc_to_usba_adapter.png"},
    {"name": "USB-C Charging Cable 2m", "category": "Electronics", "price": "6.90", "image": "products/usbc_charging_cable_2m.png"},
    {"name": "Laptop Stand Adjustable Aluminum", "category": "Electronics", "price": "19.90", "image": "products/laptop_stand_adjustable_aluminum.png"},
    {"name": "Wireless Mouse Silent Click", "category": "Electronics", "price": "12.90", "image": "products/wireless_mouse_silent_click.png"},
    {"name": "Bluetooth Earbuds Budget", "category": "Electronics", "price": "22.90", "image": "products/bluetooth_earbuds_budget.png"},
    {"name": "Portable Power Bank 10000mAh", "category": "Electronics", "price": "18.90", "image": "products/portable_power_bank_10000mah.png"},
    {"name": "Phone Tripod Mini", "category": "Electronics", "price": "10.90", "image": "products/phone_tripod_mini.png"},
    {"name": "Screen Cleaning Kit", "category": "Electronics", "price": "5.90", "image": "products/screen_cleaning_kit.png"},

    # Study / Office
    {"name": "A4 Notebook Dotted 160 Pages", "category": "Stationery", "price": "3.90", "image": "products/a4_notebook_dotted_160_pages.png"},
    {"name": "Gel Pen Set 6 Colors", "category": "Stationery", "price": "4.90", "image": "products/gel_pen_set_6_colors.png"},
    {"name": "Desk Organizer Tray Set", "category": "Stationery", "price": "11.90", "image": "products/desk_organizer_tray_set.png"},
    {"name": "Sticky Notes Value Pack", "category": "Stationery", "price": "3.50", "image": "products/sticky_notes_value_pack.png"},
    {"name": "Highlighter Pack Pastel", "category": "Stationery", "price": "4.50", "image": "products/highlighter_pack_pastel.png"},
    {"name": "Mechanical Pencil 0.5mm", "category": "Stationery", "price": "2.90", "image": "products/mechanical_pencil_05mm.png"},
    {"name": "Exam File Folder A4", "category": "Stationery", "price": "2.50", "image": "products/exam_file_folder_a4.png"},
    {"name": "Whiteboard Marker Set", "category": "Stationery", "price": "5.90", "image": "products/whiteboard_marker_set.png"},

    # Home / Lifestyle
    {"name": "Reusable Grocery Tote Bag", "category": "Home", "price": "4.90", "image": "products/reusable_grocery_tote_bag.png"},
    {"name": "Insulated Lunch Box", "category": "Home", "price": "13.90", "image": "products/insulated_lunch_box.png"},
    {"name": "Stainless Steel Cutlery Set", "category": "Home", "price": "9.90", "image": "products/stainless_steel_cutlery_set.png"},
    {"name": "Compact Umbrella Windproof", "category": "Home", "price": "10.90", "image": "products/compact_umbrella_windproof.png"},
    {"name": "Laundry Mesh Bag Set", "category": "Home", "price": "6.90", "image": "products/laundry_mesh_bag_set.png"},
    {"name": "Scented Candle Small Jar", "category": "Home", "price": "7.90", "image": "products/scented_candle_small_jar.png"},
    {"name": "Microfiber Cleaning Cloth Pack", "category": "Home", "price": "5.90", "image": "products/microfiber_cleaning_cloth_pack.png"},
    {"name": "Waterproof Phone Pouch", "category": "Home", "price": "6.50", "image": "products/waterproof_phone_pouch.png"},

    # Fitness / Wellness
    {"name": "Resistance Bands Set", "category": "Fitness", "price": "11.90", "image": "products/resistance_bands_set.png"},
    {"name": "Yoga Mat 6mm Non-Slip", "category": "Fitness", "price": "18.90", "image": "products/yoga_mat_6mm_non_slip.png"},
    {"name": "Foam Roller Compact", "category": "Fitness", "price": "14.90", "image": "products/foam_roller_compact.png"},
    {"name": "Jump Rope Adjustable", "category": "Fitness", "price": "6.90", "image": "products/jump_rope_adjustable.png"},
    {"name": "Gym Towel Quick Dry", "category": "Fitness", "price": "5.90", "image": "products/gym_towel_quick_dry.png"},
    {"name": "Shaker Bottle 600ml", "category": "Fitness", "price": "6.50", "image": "products/shaker_bottle_600ml.png"},
    {"name": "Massage Ball Set", "category": "Fitness", "price": "7.90", "image": "products/massage_ball_set.png"},
    {"name": "Smart Step Counter Clip", "category": "Fitness", "price": "12.50", "image": "products/smart_step_counter_clip.png"},
]


class Command(BaseCommand):
    help = "Seed 40 additional SmartShop products (with image file paths)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print what would be created without saving.")
        parser.add_argument("--prefix", default="", help="Optional name prefix to avoid collisions.")

    @transaction.atomic
    def handle(self, *args, **options):
        dry = bool(options["dry_run"])
        prefix = (options["prefix"] or "").strip()

        created = 0
        skipped = 0

        for item in EXTRA_PRODUCTS_40:
            name = f"{prefix}{item['name']}".strip()

            exists = SmartShopProduct.objects.filter(name=name).exists()
            if exists:
                skipped += 1
                continue

            if dry:
                self.stdout.write(self.style.WARNING(f"[DRY] would create: {name}"))
                created += 1
                continue

            p = SmartShopProduct(
                name=name,
                category=item["category"],
                price=Decimal(item["price"]),
            )

            # Set ImageField path (file must exist in MEDIA_ROOT/products/)
            # e.g. backend/media/products/compact_hiking_backpack_20l.png
            img_path = item.get("image")
            if img_path:
                p.image = img_path

            p.save()
            created += 1

        if dry:
            raise SystemExit("Dry-run complete (rolled back).")

        self.stdout.write(self.style.SUCCESS(f"✅ Done. Created: {created}, Skipped (already exists): {skipped}"))
        self.stdout.write("📌 Next: put your images into backend/media/products/ using the filenames listed.")
