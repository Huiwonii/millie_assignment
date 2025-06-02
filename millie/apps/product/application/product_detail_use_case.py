from decimal import Decimal
from typing import (
    List,
    Optional,
    Tuple,
)

from apps.pricing.application.discount_service import DiscountService
from apps.pricing.application.coupon_service import CouponService
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.product.domain.repository import ProductRepository
from apps.product.domain.value_objects import ProductStatus

from apps.utils.exceptions import NotFoundException


class ProductDetailUseCase:

    def __init__(
        self,
        product_repo: ProductRepository,
        discount_service: DiscountService,
        coupon_service: CouponService,
    ):
        self.product_repo = product_repo
        self.discount_service = discount_service
        self.coupon_service = coupon_service

    def execute(
        self,
        code: str,
        user=None,
        coupon_code=None,
    ):
        product_entity = self.product_repo.get_product_by_code(code)

        # 1) 상품 없거나 비활성 상태면 NotFoundError
        if not product_entity or product_entity.status != ProductStatus.ACTIVE.value:
            raise NotFoundException(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")

        base_price = product_entity.price

        # 2) get_applicable_coupons(): 화면으로 보여줄 후보 전체
        raw_applicable = self.coupon_service.get_applicable_coupons(
            product_code=code,
            user=user,
        ) or []

        # 3) “최소 구매 금액”과 “is_available” 체크 → 실제 화면에 보여줄 final_applicable
        final_applicable = []
        for coupon in raw_applicable:
            if base_price < coupon.minimum_purchase_amount:
                # 최소 구매 금액 미달
                continue
            if not coupon.is_available(user, product_entity.code):
                # 유효성(만료, 상태, 타겟 등) 미충족
                continue
            final_applicable.append(coupon)

        # 4) 가격 계산 로직 (coupon_code가 들어온 경우에만 적용)
        if not coupon_code:
            # coupon_code가 없으면 가격 원가 그대로
            price_result = PriceResultEntity(
                original=base_price,
                discounted=base_price,
                discount_amount=Decimal("0.00"),
                discount_types=[],
            )
            return product_entity, final_applicable, price_result

        # 5) coupon_code가 들어왔을 때, 실제 사용자가 쿼리 스트링으로 보낸 값과 final_applicable 을 매칭
        # chosen_codes = set(coupon_code)
        coupons_domain = self.coupon_service.get_coupons_by_code(coupon_code) or []

        # 6) final_applicable 중 “최종 적용 가능한 쿠폰만” price 계산에 쓰기
        final_price = base_price
        total_discount_amount = Decimal("0.00")
        discount_types: List[str] = []

        for coupon in coupons_domain:
            # (a) screen-level 걸러낸 final_applicable 에 포함되어 있고
            # (b) 실제 is_available(user, code)가 true 여야만
            if coupon.code not in {c.code for c in final_applicable}:
                continue
            if not coupon.is_available(user, product_entity.code):
                continue

            # (c) 할인을 누적 적용
            policy = coupon.to_discount_policy()
            result = policy.apply(final_price)
            total_discount_amount += (final_price - result.discounted)
            final_price = result.discounted
            discount_types.extend(result.discount_types)
            discount_types = list(set(discount_types))

        price_result = PriceResultEntity(
            original=base_price,
            discounted=final_price,
            discount_amount=total_discount_amount,
            discount_types=discount_types,
        )

        return product_entity, final_applicable, price_result

