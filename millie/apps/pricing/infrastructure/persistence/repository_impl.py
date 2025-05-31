from datetime import datetime
from django.utils import timezone
from typing import Optional

from apps.pricing.domain.entity import Coupon as CouponEntity
from apps.pricing.domain.discount_policy import (
    PriceResult,
    FixedDiscountPolicy,
    PercentageDiscountPolicy,
)
from apps.pricing.infrastructure.persistence.mapper import (
    CouponMapper,
    DiscountPolicyMapper,
)
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.infrastructure.persistence.models import DiscountPolicy as DiscountPolicyModel
from apps.pricing.infrastructure.persistence.models import DiscountTarget as DiscountTargetModel
from apps.pricing.domain.repository import CouponRepository



class CouponRepositoryImpl(CouponRepository):

    def __init__(self):
        self.coupon_mapper = CouponMapper()
        self.discount_policy_mapper = DiscountPolicyMapper()

    def get_coupon_by_code(
        self,
        coupon_code: str,
    ) -> Optional[CouponEntity]:

        coupon = CouponModel.objects.get(code=coupon_code)

        now = timezone.now()
        if coupon and coupon.valid_until >= now:
            return self.coupon_mapper.to_domain(coupon)
        return None


    def get_discount_policy_by_code(
        self,
        target_product_code: str,
    ) -> Optional[PriceResult]:


        discount_target = DiscountTargetModel.objects.filter(
            target_product_code=target_product_code,
        ).order_by("apply_priority").first()
        if not discount_target:
            return None

        policy = discount_target.discount_policy

        now = timezone.now()
        if not policy:
            return None

        if not (policy.is_active and policy.effective_start_at <= now <= policy.effective_end_at):
            return None

        if policy.discount_type == "percentage":
            return PercentageDiscountPolicy(
                discount_type=policy.discount_type,
                discount_rate=policy.value,
            )
        elif policy.discount_type == "fixed":
            return FixedDiscountPolicy(
                discount_type=policy.discount_type,
                discount_amount=policy.value,
            )
        else:
            return None