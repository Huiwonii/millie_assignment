from decimal import Decimal
from typing import (
    List,
    Optional,
)
from uuid import UUID
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.policy.condition import DiscountCondition
from apps.pricing.domain.entity.price_result import PriceResult


class ConditionalDiscountPolicy(DiscountPolicy):
    def __init__(
        self,
        base_policy: DiscountPolicy,
        conditions: List[DiscountCondition],
    ):
        self._base_policy = base_policy
        self._conditions = conditions

    def apply(
        self,
        price: Decimal,
        product_code: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> PriceResult:
        if all(cond.is_satisfied(price, product_code, user_id) for cond in self._conditions):
            return self._base_policy.apply(price)
        else:
            return PriceResult(
                original=price,
                discounted=price,
                discount_amount=Decimal("0.00"),
            )
