from django.contrib import admin
from .models import SmartShopProduct, SmartShopPurchaseOrder

@admin.register(SmartShopProduct)
class SmartShopProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price")
    search_fields = ("name", "category")
    list_filter = ("category",)

@admin.register(SmartShopPurchaseOrder)
class SmartShopPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "quantity", "purchase_date")
    search_fields = ("user__username", "product__name")
    list_filter = ("purchase_date",)
