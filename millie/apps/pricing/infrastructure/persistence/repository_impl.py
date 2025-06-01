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
from apps.pricing.infrastructure.persistence.models import DiscountPolicy as DiscountPolicyModel
from apps.pricing.domain.repository import DiscountPolicyRepository
from apps.pricing.domain.value_objects import (
    CouponStatus,
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
        """
        1) 활성 & 기간(=valid_until >= now) 체크
        2) CouponModel 을 모두 가져온 뒤, "할인 정책(DiscountPolicy) 의 target_type" 에 따라
           PRODUCT‐전용, USER‐전용, ALL‐대상을 OR 조건으로 묶어서 리턴
        """
        # 먼저 "status='active' 및 valid_until >= now" 인 쿠폰만 골라냅니다.
        coupons = CouponModel.objects.filter(
            status=CouponStatus.ACTIVE.value,  # 예: "active"
            valid_until__gte=reference_time,
            discount_policy__is_active=True,  # 정책 자체도 활성화 상태여야 함
            discount_policy__effective_start_at__lte=reference_time,
            discount_policy__effective_end_at__gte=reference_time,
        )

        # PRODUCT 전용 쿠폰: discount_policy.target_type = "PRODUCT" AND DiscountTarget 에서 target_product_code=상품코드
        # USER 전용 쿠폰:    discount_policy.target_type = "USER"    AND DiscountTarget 에서 target_user_id = 해당 유저
        # ALL 대상 쿠폰:    discount_policy.target_type = "ALL"    (DiscountTarget 없거나 target_product_code/user 모두 null)
        #
        # 단순히 CouponModel.filter(...) 한 번에 모두 잡히려면, DiscountTargetModel 에서 join 하지 않아도
        # "discount_policy__target_type='ALL'" 조건만 추가하면 됩니다. 즉 ALL 대상 쿠폰은 discount_policy.target_type=ALL 이므로,
        # status/valid_until/정책 활성화 조건만 맞으면 여기서 포함됩니다.

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

        # ──────────────────────────────────────────────────────────────
        # ① PRODUCT 전용 할인 조건
        q_product = Q(target_product_code=target_product_code)

        # ② USER 전용 할인 조건 (user_id가 전달됐을 때만 OR에 추가)
        q_user = Q()
        if target_user_id:
            q_user = Q(target_user_id=target_user_id)

        # ③ ALL 대상 할인 조건:
        #    → DiscountTarget.target_product_code IS NULL
        #    → DiscountPolicy.target_type == TargetType.ALL.value
        q_all = Q(
            target_product_code__isnull=True,
            discount_policy__target_type=TargetType.ALL.value,
        )

        # ①②③ 을 OR 로 결합
        combined_q = q_product | q_all
        if target_user_id:
            combined_q = combined_q | q_user

        # ──────────────────────────────────────────────────────────────
        # DiscountTarget 테이블에서 필터 후 우선순위 순으로 정렬
        discount_targets = (
            DiscountTargetModel.objects
                .filter(combined_q)
                .order_by("apply_priority")
        )

        policies: List[DiscountPolicy] = []

        for dt in discount_targets:
            policy_model = dt.discount_policy
            # 정책 유효성 체크: is_active 및 기간 확인
            if not (policy_model and policy_model.is_active and
                    policy_model.effective_start_at <= now <= policy_model.effective_end_at):
                continue

            # 도메인 DiscountPolicy 객체로 변환 (우선순위도 함께 전달)
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