from datetime import datetime
from uuid import UUID
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
from apps.pricing.infrastructure.persistence.models import Promotion as PromotionModel
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.repositories.promotion_repository import PromotionRepository
from apps.pricing.domain.value_objects import DiscountType


class PromotionRepoImpl(PromotionRepository):

    def get_active_promotions(
        self,
        target_product_code: Optional[str] = None,
        target_user_id: Optional[UUID] = None,
    ) -> List[DiscountPolicy]:
        now = timezone.now()

        # 조건 1: 상품 대상 프로모션
        q_product = Q(target_product_code=target_product_code)

        # 조건 2: 유저 대상 프로모션
        q_user = Q()
        if target_user_id:
            q_user = Q(target_user=target_user_id)

        # 조건 3: 전체 대상 프로모션
        q_all = Q(target_product_code__isnull=True, target_user__isnull=True)

        # 최종 쿼리: 세 조건을 OR로 묶음 + 공통조건 필터링
        combined_q = q_product | q_user | q_all

        promotions = (
            PromotionModel.objects.filter(
                combined_q,
                is_active=True,
                is_auto_discount=True,      # 자동할인 적용인것만
                effective_start_at__lte=now,
                effective_end_at__gte=now,
            ).order_by("apply_priority")
        )

        result: List[DiscountPolicy] = []
        for promo in promotions:
            policy = promo.discount_policy
            if not policy or not policy.is_active:
                continue

            if policy.discount_type == DiscountType.PERCENTAGE.value:
                result.append(
                    PercentageDiscountPolicy(
                        discount_type=policy.discount_type,
                        discount_rate=policy.value,
                    )
                )
            elif policy.discount_type == DiscountType.FIXED.value:
                result.append(
                    FixedDiscountPolicy(
                        discount_type=policy.discount_type,
                        discount_amount=policy.value,
                    )
                )

        return result
