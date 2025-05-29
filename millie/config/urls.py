from django.urls import path
from apps.product.interface.product_list_views import ProductListView

urlpatterns = [
    path("api/v1/products", ProductListView.as_view(), name="product-list"),
    # path("api/v1/products/<str:code>", ProductListView.as_view(), name="product-detail"),
]