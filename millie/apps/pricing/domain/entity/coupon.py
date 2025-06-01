from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.value_objects import CouponStatus


@dataclass
class Coupon:
    id: UUID
    code: str
    name: str
    discount_policy: DiscountPolicy
    valid_until: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    target_product_code: Optional[str] = None
    target_user_id: Optional[UUID] = None
    is_active: bool = False
    minimum_purchase_amount: Decimal = Decimal("0")

    def is_available(
        self,
        user,
        product_code,
    ) -> bool:
        if self.status != CouponStatus.ACTIVE:
            return False

        if self.target_product_code and self.target_product_code != product_code:
            return False

        if self.target_user_id and self.target_user_id != user.id:
            return False

        return True

    def to_discount_policy(self) -> DiscountPolicy:
        return self.discount_policy