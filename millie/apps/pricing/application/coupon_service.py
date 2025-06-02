from typing import (
    List,
    Optional,
)

from django.utils import timezone

from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.repository import DiscountPolicyRepository

class CouponService:
    def __init__(
        self,
        repo: DiscountPolicyRepository,
    ):
        self._repo = repo

    def get_applicable_coupons(
        self,
        product_code: str,
        user,
    ) -> List[CouponEntity]:

        now = timezone.now()
        coupons = self._repo.list_active_not_expired(now)

        result: List[CouponEntity] = []
        for coupon in coupons:
            if coupon.is_active and coupon.is_available(user, product_code):
                result.append(coupon)

        return result

    def get_coupons_by_code(
        self,
        coupon_code: List[str],
    ) -> Optional[CouponEntity]:

        coupon = self._repo.get_coupons_by_code(coupon_code)
        if not coupon:
            return None
        return coupon
