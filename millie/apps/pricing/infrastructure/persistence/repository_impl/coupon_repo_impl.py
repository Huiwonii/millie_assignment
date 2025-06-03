from datetime import datetime
from uuid import UUID
from typing import (
    List,
    Optional,
)

from django.utils import timezone

from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.infrastructure.persistence.mapper import (
    CouponMapper,
    DiscountPolicyMapper,
)
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.domain.repositories.coupon_repository import CouponRepository
from apps.pricing.domain.value_objects import CouponStatus


class CouponRepoImpl(CouponRepository):

    def __init__(self):
        self.coupon_mapper = CouponMapper()
        self.discount_policy_mapper = DiscountPolicyMapper()

    def get_coupons_by_code(
        self,
        coupon_code: List[str],
        is_valid: bool = True,
    ) -> List[Optional[CouponEntity]]:

        coupons = CouponModel.objects.filter(code__in=coupon_code)

        if is_valid:
            coupons = coupons.filter(valid_until__gte=timezone.now(), status=CouponStatus.ACTIVE.value)
        return [self.coupon_mapper.to_domain(c) for c in coupons]


    def list_active_not_expired(
        self,
        reference_time: datetime,
    ) -> List[CouponEntity]:

        coupons = CouponModel.objects.filter(
            status=CouponStatus.ACTIVE.value,
            valid_until__gte=reference_time,
            discount_policy__is_active=True,
            discount_policy__effective_start_at__lte=reference_time,
            discount_policy__effective_end_at__gte=reference_time,
        )
        return [self.coupon_mapper.to_domain(coupon) for coupon in coupons]

