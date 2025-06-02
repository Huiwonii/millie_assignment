from rest_framework.views import APIView
from rest_framework import status

from apps.product.application.product_detail_use_case import ProductDetailUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.product.interface.serializer import ProductSerializer
from apps.pricing.application.coupon_service import CouponService
from apps.pricing.application.promotion_service import PromotionService
from apps.pricing.infrastructure.persistence.repository_impl.coupon_repo_impl import CouponRepoImpl
from apps.pricing.infrastructure.persistence.repository_impl.promotion_repo_impl import PromotionRepoImpl
from apps.pricing.interface.serializer import (
    CouponSummarySerializer,
    PriceResultSerializer,
)

from apps.utils import (
    const,
    messages,
)
from apps.utils.exceptions import NotFoundException
from apps.utils.response import build_api_response


class ProductDetailView(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_case = ProductDetailUseCase(
            product_repo=ProductRepositoryImpl(),
            promotion_service=PromotionService(PromotionRepoImpl()),
            coupon_service=CouponService(CouponRepoImpl()),
        )

    def get(self, request, code: str):
        redundant_params = self._find_invalid_query_params(request)
        if redundant_params:
            return build_api_response(
                data={},
                message=f"{messages.BAD_REQUEST}: {', '.join(redundant_params)}",
                code=status.HTTP_400_BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        coupon_code = request.query_params.getlist(const.COUPON_CODE, [])
        user = request.user if getattr(request.user, "is_authenticated", False) else None

        try:
            product_entity, coupon_list, price_result = self._use_case.execute(
                code=code,
                user=user,
                coupon_code=coupon_code,
            )
        except Exception as e:
            if isinstance(e, NotFoundException):
                return build_api_response(
                    data={},
                    message=str(e),
                    code=status.HTTP_404_NOT_FOUND,
                    http_status=status.HTTP_404_NOT_FOUND,
                )
            return build_api_response(
                data={},
                message=f"{messages.INTERNAL_SERVER_ERROR}: {str(e)}",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serialized_product = ProductSerializer(product_entity).data
        serialized_coupons = CouponSummarySerializer(coupon_list, many=True).data
        serialized_price_result = PriceResultSerializer(price_result).data

        response_data = {
            const.PRODUCT: serialized_product,
            const.AVAILABLE_DISCOUNT: serialized_coupons,
            const.PRICE_CALCULATE_RESULT: serialized_price_result,
        }

        return build_api_response(
            data=response_data,
            message=messages.OK,
            code=status.HTTP_200_OK,
            http_status=status.HTTP_200_OK,
        )

    def _find_invalid_query_params(self, request) -> list:
        allowed = {const.COUPON_CODE}
        extras = set(request.query_params.keys()) - allowed
        return list(extras)
