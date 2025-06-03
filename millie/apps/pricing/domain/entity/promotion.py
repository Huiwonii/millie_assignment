from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from apps.pricing.domain.policy.discount_policy import DiscountPolicy


@dataclass
class Promotion:
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    discount_policy: DiscountPolicy
    is_auto_discount: bool
    apply_priority: int


    def to_discount_policy(self) -> DiscountPolicy:
        return self.discount_policy

