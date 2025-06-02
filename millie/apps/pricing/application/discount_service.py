from decimal import Decimal
from typing import (
    List,
    Optional,
)

from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.repository import DiscountPolicyRepository


class DiscountService:
    def __init__(
        self,
        repo: DiscountPolicyRepository,
    ):
        self._repo = repo

    def apply_policy(
        self,
        product_code: str,
        original_price: Decimal,
        user = None,
    ) -> PriceResultEntity:

        strategy_list: Optional[List[DiscountPolicy]] = self._repo.get_discount_policies(
            target_product_code=product_code,
            target_user_id=user.id if user else None,
        )
        if not strategy_list:
            return PriceResultEntity(
                original=original_price,
                discounted=original_price,
                discount_amount=Decimal("0"),
            )
        best_strategy = strategy_list[0]
        return best_strategy.apply(original_price)
