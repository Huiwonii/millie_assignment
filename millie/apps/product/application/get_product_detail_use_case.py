from decimal import Decimal
from typing import List, Optional, Tuple

from apps.pricing.application.services.coupon_service import CouponService
from apps.pricing.application.services.promotion_service import PromotionService
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.product.domain.repository import ProductRepository

from apps.utils.exceptions import NotFoundException


class GetProductDetailUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
        promotion_service: PromotionService,
        coupon_service: CouponService,
    ):
        self._product_repo = product_repo
        self._promotion_service = promotion_service
        self._coupon_service = coupon_service

    def execute(
        self,
        code: str,
        user=None,
        coupon_code: Optional[List[str]] = None,
    ) -> Tuple[ProductEntity, List[CouponEntity]]:
        """
        1) 상품 조회 및 활성 상태 검증
        2) 화면에 보여줄 “적용 가능 쿠폰” 필터링
        """
        product = self._fetch(code)
        base_price = product.price

        available_coupons = self._filter_available_coupons(product, user, base_price)

        # 쿠폰 없으면 자동 할인 결과 반환
        if not coupon_code:
            return product, available_coupons

        return product, available_coupons

    # ──────────────────────────────────────────────────────────────────────────
    # 상품 조회 및 활성 상태 검증
    # ──────────────────────────────────────────────────────────────────────────
    def _fetch(self, code: str) -> ProductEntity:
        try:
            product = self._product_repo.get_product_by_code(code)
        except Exception:
            raise NotFoundException(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")
        return product

    # ──────────────────────────────────────────────────────────────────────────
    # 화면에 보여줄 적용 가능 쿠폰 필터링
    # ──────────────────────────────────────────────────────────────────────────
    def _filter_available_coupons(
        self,
        product_entity: ProductEntity,
        user,
        base_price: Decimal,
    ) -> List[CouponEntity]:
        raw_list = self._coupon_service.get_applicable_coupons(
            product_code=product_entity.code,
            user=user,
        ) or []

        filtered: List[CouponEntity] = []
        for coupon in raw_list:
            if base_price < coupon.minimum_purchase_amount:
                continue
            if not coupon.is_available(user, product_entity.code):
                continue
            filtered.append(coupon)

        return filtered
