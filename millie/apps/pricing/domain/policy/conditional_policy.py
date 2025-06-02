from decimal import Decimal
from typing import (
    List,
    Optional,
)
from uuid import UUID

from apps.pricing.domain.policy.condition import DiscountCondition
from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity


# TODO! 현재 참조하는곳 없음 > 특정 조건을 만족하는 경우 할인을 하기 위해 만든 정책
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
    ) -> PriceResultEntity:

        if all(cond.is_satisfied(price, product_code, user_id) for cond in self._conditions):
            return self._base_policy.apply(price)

        else:
            return PriceResultEntity(
                original=price,
                discounted=price,
                discount_amount=Decimal("0.00"),
            )
