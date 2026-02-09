from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.register),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Store
    path("products/", views.products_list),

    # Purchases
    path("purchases/me/", views.my_purchases),
    path("purchases/buy/", views.buy_product),

    # AI
    path("ai/recommendations/", views.recommendations),
    path("ai/insights/", views.ai_insights),
    path("ai/smart-search/", views.smart_search),
    path("products/<int:product_id>/", views.product_detail),
    path("products/<int:product_id>/review/", views.upsert_product_review),
    
    # Product details + reviews
    path("products/<int:product_id>/", views.product_detail),
    path("products/<int:product_id>/review/", views.upsert_product_review),
    path("assistant/chat/", views.assistant_chat),
    path("assistant/reset/", views.assistant_reset),

]
