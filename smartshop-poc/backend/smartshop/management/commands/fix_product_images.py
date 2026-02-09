from django.core.management.base import BaseCommand
from smartshop.models import SmartShopProduct

FILENAME_MAP = {
    "Compact Hiking Backpack 20L": "products/compact_hiking_backpack_20l.png",
    "Stainless Steel Water Bottle 750ml": "products/stainless_steel_water_bottle_750ml.png",
    "Lightweight Rain Poncho": "products/lightweight_rain_poncho.png",
    "Portable Camping Lantern LED": "products/portable_camping_lantern_led.png",
    "Trekking Poles Pair": "products/trekking_poles_pair.png",
    "Emergency Whistle + Compass": "products/emergency_whistle_compass.png",
    "Mini First Aid Kit Travel": "products/mini_first_aid_kit_travel.png",
    "Quick-Dry Microfiber Towel": "products/quick_dry_microfiber_towel.png",

    "USB-C to USB-A Adapter": "products/usbc_to_usba_adapter.png",
    "USB-C Charging Cable 2m": "products/usbc_charging_cable_2m.png",
    "Laptop Stand Adjustable Aluminum": "products/laptop_stand_adjustable_aluminum.png",
    "Wireless Mouse Silent Click": "products/wireless_mouse_silent_click.png",
    "Bluetooth Earbuds Budget": "products/bluetooth_earbuds_budget.png",
    "Portable Power Bank 10000mAh": "products/portable_power_bank_10000mah.png",
    "Phone Tripod Mini": "products/phone_tripod_mini.png",
    "Screen Cleaning Kit": "products/screen_cleaning_kit.png",

    "A4 Notebook Dotted 160 Pages": "products/a4_notebook_dotted_160_pages.png",
    "Gel Pen Set 6 Colors": "products/gel_pen_set_6_colors.png",
    "Desk Organizer Tray Set": "products/desk_organizer_tray_set.png",
    "Sticky Notes Value Pack": "products/sticky_notes_value_pack.png",
    "Highlighter Pack Pastel": "products/highlighter_pack_pastel.png",
    "Mechanical Pencil 0.5mm": "products/mechanical_pencil_05mm.png",
    "Exam File Folder A4": "products/exam_file_folder_a4.png",
    "Whiteboard Marker Set": "products/whiteboard_marker_set.png",

    "Reusable Grocery Tote Bag": "products/reusable_grocery_tote_bag.png",
    "Insulated Lunch Box": "products/insulated_lunch_box.png",
    "Stainless Steel Cutlery Set": "products/stainless_steel_cutlery_set.png",
    "Compact Umbrella Windproof": "products/compact_umbrella_windproof.png",
    "Laundry Mesh Bag Set": "products/laundry_mesh_bag_set.png",
    "Scented Candle Small Jar": "products/scented_candle_small_jar.png",
    "Microfiber Cleaning Cloth Pack": "products/microfiber_cleaning_cloth_pack.png",
    "Waterproof Phone Pouch": "products/waterproof_phone_pouch.png",

    "Resistance Bands Set": "products/resistance_bands_set.png",
    "Yoga Mat 6mm Non-Slip": "products/yoga_mat_6mm_non_slip.png",
    "Foam Roller Compact": "products/foam_roller_compact.png",
    "Jump Rope Adjustable": "products/jump_rope_adjustable.png",
    "Gym Towel Quick Dry": "products/gym_towel_quick_dry.png",
    "Shaker Bottle 600ml": "products/shaker_bottle_600ml.png",
    "Massage Ball Set": "products/massage_ball_set.png",
    "Smart Step Counter Clip": "products/smart_step_counter_clip.png",
}

class Command(BaseCommand):
    help = "Assign image paths to products by name (for seeded products)."

    def handle(self, *args, **options):
        updated = 0
        missing = 0

        for name, img in FILENAME_MAP.items():
            p = SmartShopProduct.objects.filter(name=name).first()
            if not p:
                missing += 1
                continue

            # Only set if empty (safe)
            if not p.image:
                p.image = img
                p.save(update_fields=["image"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Updated images: {updated}"))
        self.stdout.write(self.style.WARNING(f"⚠️ Products not found: {missing}"))
