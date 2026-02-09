from django.conf import settings
from django.db import migrations


def backfill_review_user(apps, schema_editor):
    ProductReview = apps.get_model("smartshop", "ProductReview")
    UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    base_user = UserModel.objects.filter(id=1).first() or UserModel.objects.order_by("id").first()
    if not base_user:
        return

    existing_users = list(UserModel.objects.order_by("id").values_list("id", flat=True))
    user_idx = 0

    qs = ProductReview.objects.filter(user__isnull=True).order_by("product_id", "id")

    last_product_id = None
    used_user_ids_for_product = set()

    for r in qs.iterator():
        if r.product_id != last_product_id:
            last_product_id = r.product_id
            used_user_ids_for_product = set()

        chosen_user_id = None

        # pick an existing user not used for this product yet
        while user_idx < len(existing_users):
            cand = existing_users[user_idx]
            user_idx += 1
            if cand not in used_user_ids_for_product:
                chosen_user_id = cand
                break

        # create a legacy user if we run out
        if chosen_user_id is None:
            username = f"legacy_reviewer_{r.id}"
            if UserModel.objects.filter(username=username).exists():
                username = f"{username}_x"
            u = UserModel.objects.create(username=username, email="")
            try:
                u.set_unusable_password()
                u.save(update_fields=["password"])
            except Exception:
                u.password = "!"
                u.save(update_fields=["password"])

            chosen_user_id = u.id
            existing_users.append(u.id)
            user_idx = len(existing_users)

        r.user_id = chosen_user_id
        r.save(update_fields=["user_id"])
        used_user_ids_for_product.add(chosen_user_id)


class Migration(migrations.Migration):
    dependencies = [
        ("smartshop", "0008_alter_productreview_user"),
    ]

    operations = [
        migrations.RunPython(backfill_review_user, migrations.RunPython.noop),
    ]
