# apps/pricing/application/use_case.py

from typing import List, Optional
from decimal import Decimal
from django.utils import timezone

# from apps.pricing.infrastructure.persistence.repository_impl import DiscountPolicyRepoImpl
from apps.pricing.domain.repository import DiscountPolicyRepository
from apps.pricing.domain.entity.price_result import PriceResult
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyStrategy
from apps.pricing.domain.policy.discount_policy import (
    PercentageDiscountPolicy,
    FixedDiscountPolicy,
)
from apps.pricing.domain.value_objects import DiscountType
from apps.pricing.infrastructure.persistence.mapper import CouponMapper

class CouponService:
    def __init__(self, repo: DiscountPolicyRepository):
        self._repo = repo

    def get_applicable_coupons(
        self,
        product_code: str,
        user,
    ) -> List[CouponDomainEntity]:

        now = timezone.now()
        coupons = self._repo.list_active_not_expired(now)

        result: List[CouponDomainEntity] = []
        for coupon in coupons:
            if coupon.is_active and coupon.is_available(user, product_code):
                result.append(coupon)

        return result

    def get_coupons_by_code(
        self,
        coupon_code: List[str],
    ) -> Optional[CouponDomainEntity]:

        coupon = self._repo.get_coupons_by_code(coupon_code)
        if not coupon:
            return None
        return coupon
