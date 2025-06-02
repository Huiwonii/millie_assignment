# apps/product/application/product_detail_use_case.py

from typing import Optional, Tuple, List
from decimal import Decimal
from datetime import datetime

from apps.product.domain.entity import Product as ProductEntity
from apps.product.domain.repository import ProductRepository
from apps.pricing.application.discount_service import DiscountService
from apps.pricing.application.coupon_service import CouponService
from apps.pricing.domain.entity.price_result import PriceResult
from apps.product.domain.value_objects import ProductStatus
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyStrategy
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity


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
        coupon_code: Optional[str] = None,
    ) -> Tuple[ProductEntity, List[CouponDomainEntity], PriceResult]:

        product_entity: ProductEntity = self.product_repo.get_product_by_code(code)
        if not product_entity or product_entity.status != ProductStatus.ACTIVE.value:
            raise Exception(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")

        applicable_coupons = self.coupon_service.get_applicable_coupons(
            product_code=code,
            user=user,
        )

        base_price = product_entity.price
        if not coupon_code:
            return product_entity, applicable_coupons, PriceResult(
                original=base_price,
                discounted=base_price,
                discount_amount=0,
                discount_type=None,
            )
        else:

            final_price_result = PriceResult(
                original=base_price,
                discounted=base_price,
                discount_amount=0,
                discount_type=None,
            )
            coupons_domain = self.coupon_service.get_coupons_by_code(coupon_code)
            if coupons_domain is not None:
                for coupon_domain in coupons_domain:
                    if coupon_domain.is_available(user, product_entity.code):
                        strategy: DiscountPolicyStrategy = coupon_domain.to_discount_policy()
                        final_price_result = strategy.apply(final_price_result.discounted)

            return product_entity, applicable_coupons, final_price_result
