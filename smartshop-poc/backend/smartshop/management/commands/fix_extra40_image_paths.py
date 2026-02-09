from django.core.management.base import BaseCommand
from smartshop.models import SmartShopProduct

MAP = {
    "Compact Hiking Backpack 20L": "product_images/compact_hiking_backpack_20l.png",
    "Stainless Steel Water Bottle 750ml": "product_images/stainless_steel_water_bottle_750ml.png",
    "Lightweight Rain Poncho": "product_images/lightweight_rain_poncho.png",
    "Portable Camping Lantern LED": "product_images/portable_camping_lantern_led.png",
    "Trekking Poles Pair": "product_images/trekking_poles_pair.png",
    "Emergency Whistle + Compass": "product_images/emergency_whistle_compass.png",
    "Mini First Aid Kit Travel": "product_images/mini_first_aid_kit_travel.png",
    "Quick-Dry Microfiber Towel": "product_images/quick_dry_microfiber_towel.png",

    "USB-C to USB-A Adapter": "product_images/usbc_to_usba_adapter.png",
    "USB-C Charging Cable 2m": "product_images/usbc_charging_cable_2m.png",
    "Laptop Stand Adjustable Aluminum": "product_images/laptop_stand_adjustable_aluminum.png",
    "Wireless Mouse Silent Click": "product_images/wireless_mouse_silent_click.png",
    "Bluetooth Earbuds Budget": "product_images/bluetooth_earbuds_budget.png",
    "Portable Power Bank 10000mAh": "product_images/portable_power_bank_10000mah.png",
    "Phone Tripod Mini": "product_images/phone_tripod_mini.png",
    "Screen Cleaning Kit": "product_images/screen_cleaning_kit.png",

    "A4 Notebook Dotted 160 Pages": "product_images/a4_notebook_dotted_160_pages.png",
    "Gel Pen Set 6 Colors": "product_images/gel_pen_set_6_colors.png",
    "Desk Organizer Tray Set": "product_images/desk_organizer_tray_set.png",
    "Sticky Notes Value Pack": "product_images/sticky_notes_value_pack.png",
    "Highlighter Pack Pastel": "product_images/highlighter_pack_pastel.png",
    "Mechanical Pencil 0.5mm": "product_images/mechanical_pencil_05mm.png",
    "Exam File Folder A4": "product_images/exam_file_folder_a4.png",
    "Whiteboard Marker Set": "product_images/whiteboard_marker_set.png",

    "Reusable Grocery Tote Bag": "product_images/reusable_grocery_tote_bag.png",
    "Insulated Lunch Box": "product_images/insulated_lunch_box.png",
    "Stainless Steel Cutlery Set": "product_images/stainless_steel_cutlery_set.png",
    "Compact Umbrella Windproof": "product_images/compact_umbrella_windproof.png",
    "Laundry Mesh Bag Set": "product_images/laundry_mesh_bag_set.png",
    "Scented Candle Small Jar": "product_images/scented_candle_small_jar.png",
    "Microfiber Cleaning Cloth Pack": "product_images/microfiber_cleaning_cloth_pack.png",
    "Waterproof Phone Pouch": "product_images/waterproof_phone_pouch.png",

    "Resistance Bands Set": "product_images/resistance_bands_set.png",
    "Yoga Mat 6mm Non-Slip": "product_images/yoga_mat_6mm_non_slip.png",
    "Foam Roller Compact": "product_images/foam_roller_compact.png",
    "Jump Rope Adjustable": "product_images/jump_rope_adjustable.png",
    "Gym Towel Quick Dry": "product_images/gym_towel_quick_dry.png",
    "Shaker Bottle 600ml": "product_images/shaker_bottle_600ml.png",
    "Massage Ball Set": "product_images/massage_ball_set.png",
    "Smart Step Counter Clip": "product_images/smart_step_counter_clip.png",
}

class Command(BaseCommand):
    help = "Fix image paths for the extra 40 seeded products to use product_images/..."

    def handle(self, *args, **kwargs):
        updated = 0
        missing = 0
        for name, path in MAP.items():
            p = SmartShopProduct.objects.filter(name=name).first()
            if not p:
                missing += 1
                continue
            p.image = path
            p.save(update_fields=["image"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Updated: {updated} products"))
        self.stdout.write(self.style.WARNING(f"⚠️ Missing in DB: {missing} products"))
