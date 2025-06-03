from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.pricing.application.use_case.calculate_price_use_case import CalculatePriceUseCase
from apps.pricing.application.services.coupon_service import CouponService
from apps.pricing.application.services.promotion_service import PromotionService
from apps.pricing.infrastructure.persistence.repository_impl.coupon_repo_impl import CouponRepoImpl
from apps.pricing.infrastructure.persistence.repository_impl.promotion_repo_impl import PromotionRepoImpl
from apps.product.infrastructure.persistence.product_repo_impl import ProductRepoImpl
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

class CouponApplyView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_case = CalculatePriceUseCase(
            product_repo=ProductRepoImpl(),
            coupon_service=CouponService(CouponRepoImpl()),
            promotion_service=PromotionService(PromotionRepoImpl()),
        )

    def post(self, request, code: str):

        redundant_params = self._find_invalid_params(request)
        if redundant_params:
            return build_api_response(
                data={},
                message=f"{messages.BAD_REQUEST}: {', '.join(redundant_params)}",
                code=status.HTTP_400_BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        coupon_code_list = request.data.get(const.COUPON_CODE, [])
        user = request.user if getattr(request.user, "is_authenticated", False) else None   # NOTE! 실제 서비스에서는 인증된 유저 정보 전달받음


        # 상품 조회 및 검증
        try:
            product = self._use_case.fetch(code)
            self._use_case.validate(product, coupon_code_list)

            # 가격 계산 실행
            available_coupons, applied_coupons, price_result = self._use_case.execute(
                product=product,
                user=user,
                coupon_code=coupon_code_list,
            )
        except NotFoundException as e:
            return build_api_response(
                data={},
                message=str(e),
                code=status.HTTP_404_NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:                       # NOTE! 실제 서비스에서는 이렇게 예외처리 하지 않고 더 세밀히 해야함
            return build_api_response(
                data={},
                message=f"{messages.INTERNAL_SERVER_ERROR}: {str(e)}",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return build_api_response(
            data={
                "price_result": PriceResultSerializer(price_result).data,
                "available_coupons": CouponSummarySerializer(available_coupons, many=True).data,
                "applied_pricing_policies": applied_coupons,
            },
            message=messages.OK,
            code=status.HTTP_200_OK,
            http_status=status.HTTP_200_OK,
        )

    def _find_invalid_params(self, request) -> list:
        allowed = {const.COUPON_CODE}
        extras = set(request.data.keys()) - allowed
        return list(extras)
