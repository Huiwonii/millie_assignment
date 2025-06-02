from decimal import Decimal
from typing import List, Optional, Tuple

from apps.pricing.application.coupon_service import CouponService
from apps.pricing.application.promotion_service import PromotionService
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.product.domain.repository import ProductRepository

from apps.utils.exceptions import NotFoundException


class ProductDetailUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
        promotion_service: PromotionService,
        coupon_service: CouponService,
    ):
        self._product_repo = product_repo
        self._promotion_service = promotion_service
        self._coupon_service = coupon_service

    # TODO! execute 함수 코드 리팩토링 필요
    def execute(
        self,
        code: str,
        user=None,
        coupon_code: Optional[List[str]] = None,
    ) -> Tuple[ProductEntity, List[CouponEntity], PriceResultEntity]:
        """
        1) 상품 조회 및 활성 상태 검증
        2) 화면에 보여줄 “적용 가능 쿠폰” 필터링
        3) coupon_code 가 없으면 원가 그대로 반환
        4) coupon_code 가 있으면, 실제로 적용할 쿠폰만 골라서 누적 할인 계산
        """
        product = self._fetch_and_validate_product(code)
        base_price = product.price

        available_coupons = self._filter_available_coupons(product, user, base_price)

        # 프로모션 등 자동 할인 적용
        auto_discount_result = self._promotion_service.apply_policy(
            product_code=code,
            original_price=base_price,
            user=user,
        )

        # 쿠폰 없으면 자동 할인 결과 반환
        if not coupon_code:
            return product, available_coupons, auto_discount_result

        # 쿠폰 적용이 있으면 자동 할인 이후 누적 계산
        applied_codes = set(coupon_code)
        return product, available_coupons, self._calculate_price_with_coupons(
            product, user, auto_discount_result, available_coupons, applied_codes
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 상품 조회 및 활성 상태 검증
    # ──────────────────────────────────────────────────────────────────────────
    def _fetch_and_validate_product(self, code: str) -> ProductEntity:
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

    # ──────────────────────────────────────────────────────────────────────────
    # coupon_code 가 없을 때 원가 그대로 PriceResult 생성
    # ──────────────────────────────────────────────────────────────────────────
    def _build_no_discount_result(self, base_price: Decimal) -> PriceResultEntity:
        return PriceResultEntity(
            original=base_price,
            discounted=base_price,
            discount_amount=Decimal("0.00"),
            discount_types=[],
        )

    # ──────────────────────────────────────────────────────────────────────────
    # coupon_code 가 있을 때 실제 적용 쿠폰만 골라 누적 할인 계산
    # ──────────────────────────────────────────────────────────────────────────
    def _calculate_price_with_coupons(
        self,
        product_entity: ProductEntity,
        user,
        initial_result: PriceResultEntity,
        available_coupons: List[CouponEntity],
        applied_codes: set,
    ) -> PriceResultEntity:
        allowed_code_set = {c.code for c in available_coupons}
        coupons_to_apply = self._coupon_service.get_coupons_by_code(list(applied_codes)) or []

        final_price = initial_result.discounted
        total_discount_amount = initial_result.discount_amount
        accumulated_types: List[str] = list(initial_result.discount_types)

        for coupon in coupons_to_apply:
            if coupon.code not in allowed_code_set:
                continue
            if not coupon.is_available(user, product_entity.code):
                continue

            policy: DiscountPolicy = coupon.to_discount_policy()
            result = policy.apply(final_price)

            total_discount_amount += (final_price - result.discounted)
            final_price = result.discounted
            accumulated_types.extend(result.discount_types)

        unique_types = list(dict.fromkeys(accumulated_types))

        return PriceResultEntity(
            original=initial_result.original,
            discounted=final_price,
            discount_amount=total_discount_amount,
            discount_types=unique_types,
        )