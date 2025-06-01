from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.product.application.product_detail_use_case import ProductDetailUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.pricing.application.discount_service import DiscountService, CouponService
from apps.product.interface.serializer import ProductSerializer
from apps.pricing.interface.serializer import CouponSummarySerializer, PriceResultSerializer


class ProductDetailView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product_repo = ProductRepositoryImpl()
        self.discount_service = DiscountService()
        self.coupon_service = CouponService()
        self.use_case = ProductDetailUseCase(
            product_repo=self.product_repo,
            discount_service=self.discount_service,
            coupon_service=self.coupon_service,
        )

    def get(self, request, code: str):
        """
        GET /api/v1/products/{code}?coupon_code=XYZ

        Response format:
        {
          "code": 200,
          "message": "OK",
          "data": {
             "product": { ... },
             "available_coupons": [ {...}, {...} ],
             "price_result": { ... }
          }
        }
        """
        # 1) query params
        coupon_code = request.query_params.get("coupon_code", None)
        user = request.user if request.user.is_authenticated else None

        try:
            product_entity, coupon_list, price_result = self.use_case.execute(
                code=code,
                user=user,
                coupon_code=coupon_code,
            )
        except Exception as e:
            return Response(
                {
                    "code": 404,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2) 직렬화
        serialized_product = ProductSerializer(product_entity).data
        serialized_coupons = CouponSummarySerializer(coupon_list, many=True).data
        serialized_price_result = PriceResultSerializer(price_result).data

        # 3) 합쳐서 응답
        return Response(
            {
                "code": 200,
                "message": "OK",
                "data": {
                    "product": serialized_product,
                    "available_coupons": serialized_coupons,
                    "price_result": serialized_price_result,
                },
            },
            status=status.HTTP_200_OK,
        )
