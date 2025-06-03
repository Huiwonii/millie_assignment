from datetime import datetime
from uuid import UUID
from typing import (
    List,
    Optional,
)

from django.db.models import Q, OuterRef, Subquery, IntegerField
from django.utils import timezone


from apps.pricing.domain.entity.promotion import Promotion as PromotionEntity
from apps.pricing.domain.policy.discount_policy import (
    FixedDiscountPolicy,
    PercentageDiscountPolicy,
)
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.repositories.promotion_repository import PromotionRepository
from apps.pricing.domain.value_objects import DiscountType
from apps.pricing.infrastructure.persistence.mapper import PromotionMapper
from apps.pricing.infrastructure.persistence.models import (
    Promotion as PromotionModel,
    DiscountTarget as DiscountTargetModel,
)


class PromotionRepoImpl(PromotionRepository):


    def __init__(self):
        self.promotion_mapper = PromotionMapper()

    # def get_active_promotions(
    #     self,
    #     target_product_code: Optional[str] = None,
    #     target_user_id: Optional[UUID] = None,
    # ) -> List[DiscountPolicy]:
    #     now = timezone.now()

    #     target_q = Q()

    #     if target_product_code:
    #         target_q |= Q(target_product_code=target_product_code)

    #     if target_user_id:
    #         target_q |= Q(target_user=target_user_id)

    #     target_q |= Q(target_product_code__isnull=True, target_user__isnull=True)

    #     discount_target_qs = DiscountTarget.objects.filter(
    #         discount_policy=OuterRef('discount_policy_id')
    #     ).filter(target_q).order_by('apply_priority')

    #     promotions = (
    #         PromotionModel.objects.filter(
    #             is_auto_discount=True,          # 자동할인 적용인것만
    #         ).annotate(
    #             target_priority=Subquery(
    #                 discount_target_qs.values('apply_priority')[:1],
    #                 output_field=IntegerField()
    #             )
    #         ).order_by('target_priority')
    #     )

    #     result: List[DiscountPolicy] = []
    #     for promotion in promotions:
    #         policy = promotion.discount_policy
    #         if not policy or not policy.is_active:
    #             continue

    #         if policy.discount_type == DiscountType.PERCENTAGE.value:
    #             result.append(
    #                 PercentageDiscountPolicy(
    #                     discount_type=policy.discount_type,
    #                     discount_rate=policy.value,
    #                 )
    #             )
    #         elif policy.discount_type == DiscountType.FIXED.value:
    #             result.append(
    #                 FixedDiscountPolicy(
    #                     discount_type=policy.discount_type,
    #                     discount_amount=policy.value,
    #                 )
    #             )

    #     return result



    def get_active_promotions(
        self,
        target_product_code: Optional[str] = None,
        target_user_id: Optional[UUID] = None,
    ) -> List[Optional[PromotionEntity]]:


        target_q = Q()

        if target_product_code:
            target_q |= Q(target_product_code=target_product_code)

        if target_user_id:
            target_q |= Q(target_user=target_user_id)

        target_q |= Q(target_product_code__isnull=True, target_user__isnull=True)

        discount_target_qs = DiscountTargetModel.objects.filter(
            discount_policy=OuterRef('discount_policy_id')
        ).filter(target_q).order_by('apply_priority')

        promotions = (
            PromotionModel.objects.filter(
                is_auto_discount=True,          # 자동할인 적용인것만
            ).annotate(
                target_priority=Subquery(
                    discount_target_qs.values('apply_priority')[:1],
                    output_field=IntegerField()
                )
            ).order_by('target_priority')
        )

        return [self.promotion_mapper.to_domain(promotion) for promotion in promotions]

        # result: List[DiscountPolicy] = []
        # for promotion in promotions:
        #     policy = promotion.discount_policy
        #     if not policy or not policy.is_active:
        #         continue

        #     if policy.discount_type == DiscountType.PERCENTAGE.value:
        #         result.append(
        #             PercentageDiscountPolicy(
        #                 discount_type=policy.discount_type,
        #                 discount_rate=policy.value,
        #             )
        #         )
        #     elif policy.discount_type == DiscountType.FIXED.value:
        #         result.append(
        #             FixedDiscountPolicy(
        #                 discount_type=policy.discount_type,
        #                 discount_amount=policy.value,
        #             )
        #         )

        # return result
