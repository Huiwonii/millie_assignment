from datetime import datetime
from typing import (
    List,
    Optional,
)

from django.db.models import Q
from django.utils import timezone


from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.policy.discount_policy import (
    FixedDiscountPolicy,
    PercentageDiscountPolicy,
)
from apps.pricing.infrastructure.persistence.mapper import (
    CouponMapper,
    DiscountPolicyMapper,
)
from apps.pricing.infrastructure.persistence.models import(
    Coupon as CouponModel,
    DiscountTarget as DiscountTargetModel,
    # DiscountPolicy as DiscountPolicyModel,
)
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.repository import DiscountPolicyRepository
from apps.pricing.domain.value_objects import (
    CouponStatus,
    DiscountType,
    TargetType,
)



class DiscountPolicyRepoImpl(DiscountPolicyRepository):

    def __init__(self):
        self.coupon_mapper = CouponMapper()
        self.discount_policy_mapper = DiscountPolicyMapper()

    def get_coupons_by_code(
        self,
        coupon_code: List[str],
    ) -> Optional[CouponEntity]:

        coupons = CouponModel.objects.filter(code__in=coupon_code)
        return [self.coupon_mapper.to_domain(c) for c in coupons if c.valid_until >= timezone.now()]


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


    def get_discount_policies(
        self,
        target_product_code: str,
        target_user_id: Optional[str] = None,
    ) -> List[DiscountPolicy]:
        """
        1) 상품 전용 할인    (DiscountTarget.target_product_code == target_product_code)
        2) 사용자 전용 할인  (DiscountTarget.target_user_id      == target_user_id)
        3) ALL 대상 할인     (DiscountTarget.target_product_code is NULL && 연결된 DiscountPolicy.target_type == ALL)
        위 세 가지를 모두 OR 조건으로 묶어서 한 번에 가져온 뒤, 
        apply_priority 오름차순 정렬 → "유효한(활성+기간)" 정책만 도메인 전략 객체(Percentage/Fixed)로 매핑해 반환
        """

        now = timezone.now()

        q_product = Q(target_product_code=target_product_code)

        q_user = Q()
        if target_user_id:
            q_user = Q(target_user_id=target_user_id)

        q_all = Q(
            target_product_code__isnull=True,
            discount_policy__target_type=TargetType.ALL.value,
        )

        combined_q = q_product | q_all
        if target_user_id:
            combined_q = combined_q | q_user

        discount_targets = (
            DiscountTargetModel.objects
                .filter(combined_q)
                .order_by("apply_priority")
        )

        policies: List[DiscountPolicy] = []
        for dt in discount_targets:
            policy_model = dt.discount_policy
            if not (policy_model and policy_model.is_active and
                    policy_model.effective_start_at <= now <= policy_model.effective_end_at):
                continue

            if policy_model.discount_type == DiscountType.PERCENTAGE.value:
                policies.append(PercentageDiscountPolicy(
                    discount_type=policy_model.discount_type,
                    discount_rate=policy_model.value,
                ))
            elif policy_model.discount_type == DiscountType.FIXED.value:
                policies.append(FixedDiscountPolicy(
                    discount_type=policy_model.discount_type,
                    discount_amount=policy_model.value,
                ))

        return policies