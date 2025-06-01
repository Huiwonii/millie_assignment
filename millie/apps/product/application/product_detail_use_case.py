# apps/product/application/product_detail_use_case.py

from typing import Optional, Tuple, List
from decimal import Decimal
from datetime import datetime

from apps.product.domain.entity import Product as ProductEntity
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.pricing.application.discount_service import DiscountService
from apps.pricing.application.discount_service import CouponService
from apps.pricing.domain.entity.price_result import PriceResult
from apps.product.domain.value_objects import ProductStatus
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyStrategy
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity


class ProductDetailUseCase:
    def __init__(
        self,
        product_repo: ProductRepositoryImpl,
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
        base_price_result: PriceResult = self.discount_service.apply_best_policy(
            product_code=code,
            user=user,
            original_price=base_price,
        )

        final_price_result = base_price_result
        if coupon_code:
            coupon_domain = self.coupon_service.get_coupon_by_code(coupon_code)
            if coupon_domain is not None:
                if coupon_domain.is_available(user, product_entity.code):
                    strategy: DiscountPolicyStrategy = coupon_domain.to_discount_policy()
                    final_price_result = strategy.apply(base_price_result.discounted)
                # else:
                    # 쿠폰은 존재하지만 “이 상품/사용자에는 못 쓰는 쿠폰”이므로 그냥 무시
                    # final_price_result = base_price_result
            # else:
                # coupon_domain is None인 경우(코드가 틀렸거나 이미 만료되었거나) 무시
                # final_price_result = base_price_result

        return product_entity, applicable_coupons, final_price_result
