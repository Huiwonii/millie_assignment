from django.urls import path
from apps.product.interface.views.product_list_views import ProductListView
from apps.product.interface.views.product_detail_views import ProductDetailView
from apps.pricing.interface.views.coupon_apply_views import CouponApplyView

urlpatterns = [
    path("api/v1/products", ProductListView.as_view(), name="product-list"),
    path("api/v1/products/<str:code>", ProductDetailView.as_view(), name="product-detail"),
    path("api/v1/pricing/apply-coupon/<str:code>", CouponApplyView.as_view(), name="apply-coupon"),
]