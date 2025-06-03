from decimal import Decimal
from typing import List, Optional, Tuple

from apps.pricing.application.coupon_service import CouponService
from apps.pricing.application.promotion_service import PromotionService
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.product.domain.value_objects import ProductStatus
from apps.product.domain.repository import ProductRepository

from apps.utils.exceptions import NotFoundException


class CalculatePriceUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
        promotion_service: PromotionService,
        coupon_service: CouponService,
    ):
        self._product_repo = product_repo
        self._promotion_service = promotion_service
        self._coupon_service = coupon_service

    # ──────────────────────────────────────────────────────────────────────────
    # 상품 조회
    # ──────────────────────────────────────────────────────────────────────────

    def fetch(self, code: str) -> ProductEntity:
        product = self._product_repo.get_product_by_code(code)
        if not product:
            raise NotFoundException(f"해당 코드({code})의 상품이 존재하지 않습니다.")
        return product

    # ──────────────────────────────────────────────────────────────────────────
    # 상품 상태 검증
    # ──────────────────────────────────────────────────────────────────────────

    def validate(
        self,
        product: ProductEntity,
        coupon_code_list: List[str],
    ) -> None:
        self._validate_product_status(product)
        self._validate_valid_coupon_exists(product, coupon_code_list)


    def _validate_product_status(self, product: ProductEntity) -> None:
        if product.status != ProductStatus.ACTIVE.value:
            raise NotFoundException(f"해당 코드({product.code})의 상품은 현재 비활성 상태입니다.")


    def _validate_valid_coupon_exists(
        self,
        product: ProductEntity,
        coupon_code_list: List[str],
    ) -> None:
        if not coupon_code_list:
            return

        coupon = self._coupon_service.get_coupons_by_code(
            coupon_code=coupon_code_list,
            is_valid=True,
        )
        if not coupon:
            raise NotFoundException(f"해당 코드({coupon_code_list})의 쿠폰이 존재하지 않습니다.")

    # ──────────────────────────────────────────────────────────────────────────
    # 쿠폰 적용
    # ──────────────────────────────────────────────────────────────────────────

    def execute(
        self,
        product: ProductEntity,
        user=None,
        coupon_code: Optional[List[str]] = None,
    ) -> Tuple[List[CouponEntity], List[CouponEntity], PriceResultEntity]:
        base_price = product.price

        available_coupons = self._filter_available_coupons(product, user, base_price)
        auto_discount_result, has_promotion, promotion_name = self._promotion_service.apply_policy(
            product_code=product.code,
            original_price=base_price,
            user=user,
        )
        applied_codes = set(coupon_code) if coupon_code else set()

        if not coupon_code and not has_promotion:
            return available_coupons, [], auto_discount_result

        price_result, applied_coupons = self._calculate_price_with_coupons(
            product, user, auto_discount_result, available_coupons, applied_codes
        )
        if has_promotion:
            applied_coupons.append(promotion_name)

        return available_coupons, applied_coupons, price_result


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

    def _calculate_price_with_coupons(
        self,
        product_entity: ProductEntity,
        user,
        initial_result: PriceResultEntity,
        available_coupons: List[CouponEntity],
        applied_codes: set,
    ) -> Tuple[PriceResultEntity, List[str]]:
        allowed_code_set = {c.code for c in available_coupons}
        coupons_to_apply = self._coupon_service.get_coupons_by_code(list(applied_codes)) or []

        final_price = initial_result.discounted
        total_discount_amount = initial_result.discount_amount
        accumulated_types: List[str] = list(initial_result.discount_types)

        applied_coupons: List[CouponEntity] = []
        for coupon in coupons_to_apply:
            if coupon.code not in allowed_code_set:
                continue
            if not coupon.is_available(user, product_entity.code):
                continue
            applied_coupons.append(coupon.name)
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
        ), applied_coupons
