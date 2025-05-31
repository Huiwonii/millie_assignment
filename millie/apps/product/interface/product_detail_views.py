from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.product.application.use_case import ProductDetailUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.pricing.application.service import PricingService
from apps.pricing.infrastructure.persistence.repository_impl import CouponRepositoryImpl
from apps.product.interface.serializer import ProductDetailSerializer
from apps.utils import const

class ProductDetailView(APIView):
    def __init__(self, **kwargs):

        self.pricing_service = PricingService(
            coupon_repo=CouponRepositoryImpl(),
            product_repo=ProductRepositoryImpl(),
        )

    def get(self, request, code):
        coupon_code = request.query_params.get("coupon_code")
        product_detail = self.pricing_service.calculate_final_price(
            product_code=code,
            coupon_code=coupon_code,
        )
        if not product_detail:
            return Response(
                {
                    const.CODE: status.HTTP_404_NOT_FOUND,
                    const.MESSAGE: "No product found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                const.CODE: status.HTTP_200_OK,
                const.MESSAGE: "OK.",
                const.DATA: ProductDetailSerializer(product_detail).data,
            },
            status=status.HTTP_200_OK,
        )