from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.utils import timezone

from apps.pricing.domain.policy.discount_policy import DiscountPolicy
from apps.pricing.domain.value_objects import (
    CouponStatus,
    TargetType,
)


@dataclass
class Coupon:
    id: UUID
    code: str
    name: str
    discount_policy: DiscountPolicy
    valid_until: datetime
    status: CouponStatus
    created_at: datetime
    updated_at: datetime
    target_type: TargetType
    target_product_code: Optional[str]
    target_user_id: Optional[UUID]
    minimum_purchase_amount: Decimal
    is_active: bool = False
    apply_priority: int = 0

    @property
    def discount_type(self):
        if self.discount_policy is None:
            return None
        return self.discount_policy.discount_type

    @property
    def discount_value(self) -> Decimal:
        if self.discount_policy is None:
            return None
        return self.discount_policy.value


    def is_available(self, user, product_code: str) -> bool:
        now = timezone.now()

        if self.status != CouponStatus.ACTIVE.value or self.valid_until < now:
            return False

        def product_code_match():
            coupon_code = str(self.target_product_code) if self.target_product_code is not None else None
            prod_code = str(product_code) if product_code is not None else None
            return coupon_code == prod_code

        checks = {
            TargetType.ALL.value: lambda: True,
            TargetType.PRODUCT.value: product_code_match,
            TargetType.USER.value: lambda: self.target_user_id == getattr(user, 'id', None),
        }
        return checks.get(self.target_type, lambda: False)()


    def to_discount_policy(self) -> DiscountPolicy:
        return self.discount_policy