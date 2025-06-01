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


# @dataclass
# class Coupon:
#     id: UUID
#     code: str
#     name: str
#     discount_policy: DiscountPolicy
#     valid_until: datetime
#     status: str
#     created_at: datetime
#     updated_at: datetime
#     target_product_code: Optional[str] = None
#     target_user_id: Optional[UUID] = None
#     is_active: bool = False
#     minimum_purchase_amount: Decimal = Decimal("0")


#     def is_available(self, user, product_code: str) -> bool:
#         """
#         1) 쿠폰 상태(status)가 'active' 여야 함
#         2) 유효 기간(valid_until) 검사
#         3) discount_policy.target_type 에 따라 PRODUCT/USER/ALL 검사
#         """
#         now = timezone.now()
#         if self.status != CouponStatus.ACTIVE.value:
#             return False
#         if self.valid_until < now:
#             return False

#         policy = self.discount_policy  # DiscountPolicyDomainEntity (전략 객체)라면 내부에 target_type 정보가 로그인되어 있어야 함.
#         # 진짜는 policy 객체 안에 target_type, target_product_code, target_user_id 등이 보관되어 있어야 함.
#         if policy.target_type == TargetType.ALL.value:
#             return True

#         if policy.target_type == TargetType.PRODUCT.value:
#             # 도메인 엔티티에 product 전용인지 저장해 두었다면:
#             return self.target_product_code == product_code

#         if policy.target_type == TargetType.USER.value:
#             # 도메인 엔티티에 user 전용인지 저장해 두었다면:
#             return self.target_user_id == user.id

#         return False


#     def to_discount_policy(self) -> DiscountPolicy:
#         return self.discount_policy



@dataclass
class Coupon:
    id: UUID
    code: str
    name: str
    discount_policy: DiscountPolicy    # 이미 전략 객체
    valid_until: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    # → 할인 대상 정보를 Coupon 자체가 들고 있어야 한다
    target_type: str                  # ALL / PRODUCT / USER
    target_product_code: Optional[str]
    target_user_id: Optional[UUID]
    minimum_purchase_amount: Decimal
    # (더 필요하다면 apply_priority 등도)
    is_active: bool = False

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
        if self.status != CouponStatus.ACTIVE.value:
            return False
        if self.valid_until < now:
            return False

        # 이제 "self.target_type"을 검사해야지,
        # self.discount_policy 안에는 절대 target_type이 없으므로
        if self.target_type == TargetType.ALL.value:
            return True

        if self.target_type == TargetType.PRODUCT.value:
            return (self.target_product_code == product_code)

        if self.target_type == TargetType.USER.value:
            return (self.target_user_id == user.id)

        return False

    def to_discount_policy(self) -> DiscountPolicy:
        return self.discount_policy