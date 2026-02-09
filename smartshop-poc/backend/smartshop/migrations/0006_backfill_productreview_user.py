from django.conf import settings
from django.db import migrations


def backfill_review_user(apps, schema_editor):
    ProductReview = apps.get_model("smartshop", "ProductReview")
    UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    # Ensure we have at least one user
    base_user = UserModel.objects.filter(id=1).first() or UserModel.objects.order_by("id").first()
    if not base_user:
        # No users exist; cannot backfill safely
        return

    # Get all reviews missing user, ordered for deterministic assignment
    qs = ProductReview.objects.filter(user__isnull=True).order_by("product_id", "id")

    # We'll reuse existing users first (so we don't create too many)
    existing_users = list(UserModel.objects.order_by("id").values_list("id", flat=True))
    user_idx = 0

    last_product_id = None
    used_user_ids_for_product = set()

    for r in qs.iterator():
        # New product group => reset set
        if r.product_id != last_product_id:
            last_product_id = r.product_id
            used_user_ids_for_product = set()

        # Pick a user id that hasn't been used for this product yet
        chosen_user_id = None

        # Try existing users
        while user_idx < len(existing_users):
            cand = existing_users[user_idx]
            user_idx += 1
            if cand not in used_user_ids_for_product:
                chosen_user_id = cand
                break

        # If not enough existing users, create a unique "legacy" user
        if chosen_user_id is None:
            username = f"legacy_reviewer_{r.id}"
            # Ensure username is unique (very defensive)
            if UserModel.objects.filter(username=username).exists():
                username = f"{username}_x"

            u = UserModel.objects.create(username=username, email="")
            # Make password unusable if method exists (works on Django User model)
            try:
                u.set_unusable_password()
                u.save(update_fields=["password"])
            except Exception:
                # fallback
                u.password = "!"
                u.save(update_fields=["password"])

            chosen_user_id = u.id
            existing_users.append(u.id)
            user_idx = len(existing_users)  # keep pointer consistent

        # Assign and save
        r.user_id = chosen_user_id
        r.save(update_fields=["user_id"])

        used_user_ids_for_product.add(chosen_user_id)


class Migration(migrations.Migration):
    dependencies = [
        # keep your corrected dependency here
        ("smartshop", "0005_alter_productreview_options_productreview_updated_at_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_review_user, migrations.RunPython.noop),
    ]
