from decimal import Decimal
from typing import (
    List,
    Optional,
    Tuple,
)

from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.repositories.promotion_repository import PromotionRepository


class PromotionService:
    def __init__(
        self,
        repo: PromotionRepository,
    ):
        self._repo = repo

    def apply_policy(
        self,
        product_code: str,
        original_price: Decimal,
        user = None,
    ) -> Tuple[PriceResultEntity, bool]:
        # NOTE!
        # 프로모션 코드이면서 쿠폰 코드인것은 없다고 가정하였습니다.
        # 한 상품에 적용되는 프로모션 할인은 우선선위 높은것 하나만 가져오도록 하였습니다.

        has_promotion = False
        strategy_list = self._repo.get_active_promotions(
            target_product_code=product_code,
            target_user_id=user.id if user else None,
        )
        if not strategy_list:
            return PriceResultEntity(
                original=original_price,
                discounted=original_price,
                discount_amount=Decimal("0"),
            ), False, None

        has_promotion = True
        promotion = strategy_list[0]
        applied_promotion = promotion.name

        return promotion.to_discount_policy().apply(original_price), has_promotion, applied_promotion
