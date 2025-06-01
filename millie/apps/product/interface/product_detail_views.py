from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.product.application.product_detail_use_case import ProductDetailUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.pricing.infrastructure.persistence.repository_impl import DiscountPolicyRepoImpl
from apps.pricing.application.discount_service import DiscountService
from apps.pricing.application.coupon_service import CouponService
from apps.product.interface.serializer import ProductSerializer
from apps.pricing.interface.serializer import CouponSummarySerializer, PriceResultSerializer


class ProductDetailView(APIView):
    def __init__(self, **kwargs):
        self._use_case = ProductDetailUseCase(
            product_repo=ProductRepositoryImpl(),
            discount_service=DiscountService(DiscountPolicyRepoImpl()),
            coupon_service=CouponService(DiscountPolicyRepoImpl()),
        )

    def get(self, request, code: str):
        coupon_code = request.query_params.getlist("coupon_code", [])
        user = request.user if request.user.is_authenticated else None

        try:
            product_entity, coupon_list, price_result = self._use_case.execute(
                code=code,
                user=user,
                coupon_code=coupon_code,
            )
        except Exception as e:
            return Response(
                {
                    "code": 404,
                    "message": str(e),
                    "data": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )


        serialized_product = ProductSerializer(product_entity).data
        serialized_coupons = CouponSummarySerializer(coupon_list, many=True).data
        serialized_price_result = PriceResultSerializer(price_result).data

        return Response(
            {
                "code": 200,
                "message": "OK",
                "data": {
                    "product": serialized_product,
                    "available_discounts": serialized_coupons,
                    "price_result": serialized_price_result,
                },
            },
            status=status.HTTP_200_OK,
        )
