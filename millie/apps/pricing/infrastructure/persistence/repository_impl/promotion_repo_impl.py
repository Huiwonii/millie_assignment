from uuid import UUID
from typing import (
    List,
    Optional,
)

from django.db.models import (
    IntegerField,
    OuterRef,
    Q,
    Subquery,
)


from apps.pricing.domain.entity.promotion import Promotion as PromotionEntity
from apps.pricing.domain.repositories.promotion_repository import PromotionRepository
from apps.pricing.infrastructure.persistence.mapper import PromotionMapper
from apps.pricing.infrastructure.persistence.models import (
    Promotion as PromotionModel,
    DiscountTarget as DiscountTargetModel,
)


class PromotionRepoImpl(PromotionRepository):


    def __init__(self):
        self.promotion_mapper = PromotionMapper()


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
