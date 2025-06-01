from datetime import datetime
from uuid import UUID
from django.utils import timezone
from django.db.models import Q

from typing import (
    List,
    Optional,
)

from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult
from apps.pricing.domain.policy.discount_policy import (
    FixedDiscountPolicy,
    PercentageDiscountPolicy,
)
from apps.pricing.infrastructure.persistence.mapper import (
    CouponMapper,
    DiscountPolicyMapper,
)
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.infrastructure.persistence.models import DiscountTarget as DiscountTargetModel
from apps.pricing.domain.repository import DiscountPolicyRepository
from apps.pricing.domain.value_objects import (
    DiscountType,
    TargetType,
)
from apps.pricing.domain.policy.discount_policy import DiscountPolicy


class DiscountPolicyRepoImpl(DiscountPolicyRepository):

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


    # def get_discount_policies(
    #     self,
    #     target_product_code: str,
    #     user_id: Optional[UUID] = None,
    # ) -> Optional[List[PriceResult]]:

    #     discount_targets = DiscountTargetModel.objects.filter(
    #         target_product_code=target_product_code,
    #     ).order_by("apply_priority")

    #     result = []
    #     for discount_target in discount_targets:
    #         policy = discount_target.discount_policy
    #         if not policy or not (policy.is_active and policy.effective_start_at <= timezone.now() <= policy.effective_end_at):
    #             continue

    #         if policy.discount_type == DiscountType.PERCENTAGE.value:
    #             result.append(PercentageDiscountPolicy(
    #                 discount_type=policy.discount_type,
    #                 discount_rate=policy.value,
    #             ))
    #         elif policy.discount_type == DiscountType.FIXED.value:
    #             result.append(FixedDiscountPolicy(
    #                 discount_type=policy.discount_type,
    #                 discount_amount=policy.value,
    #             ))
    #     return result


    def list_active_not_expired(
        self,
        reference_time: datetime,
    ) -> List[CouponEntity]:
        coupons = CouponModel.objects.filter(
            valid_until__gte=reference_time,
            status="ACTIVE",
        )
        return [self.coupon_mapper.to_domain(coupon) for coupon in coupons]

    def get_discount_policies(
        self,
        target_product_code: str,
        target_user_id: Optional[str] = None,
    ) -> List[DiscountPolicy]:
        """
        1) 상품 전용 할인 (DiscountTarget.target_product_code = target_product_code)
        2) 사용자 전용 할인 (DiscountTarget.target_user_id      = target_user_id)
        두 가지를 모두 가져와서, apply_priority 순으로 정렬 후 유효한 정책만 도메인 객체로 반환
        """

        # 1) Q 객체로 필터 조건을 하나로 묶어줍니다.
        #    - 상품 전용: target_product_code=target_product_code
        #    - 사용자 전용: target_user_id=target_user_id (None이면 이 조건은 무시됨)
        query = Q(target_product_code=target_product_code)
        if target_user_id:
            query = query | Q(target_user_id=target_user_id)

        discount_targets = DiscountTargetModel.objects.filter(query).order_by("apply_priority")

        all_targets = DiscountTargetModel.objects.filter(
            target_product_code__isnull=True,
            target_user_id__isnull=True,
            discount_policy__target_type=TargetType.ALL.value,
        )
        discount_targets = list(discount_targets) + list(all_targets)

        policies: List[DiscountPolicy] = []
        now = timezone.now()

        for dt in discount_targets:
            policy_model = dt.discount_policy
            # 정책 유효성 체크: is_active 및 기간 확인
            if not (policy_model and policy_model.is_active and
                    policy_model.effective_start_at <= now <= policy_model.effective_end_at):
                continue

            # 도메인 DiscountPolicy 객체로 변환
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
