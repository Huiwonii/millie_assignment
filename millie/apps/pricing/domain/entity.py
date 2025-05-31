from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from apps.pricing.domain.discount_policy import DiscountPolicy

@dataclass
class Coupon:

    """
    쿠폰이 아무리 다양해진다고 해도 
    - 쿠폰 고유 ID, 
    - 쿠폰 이름
    - 할인 정책(정액형 쿠폰, 정률형 쿠폰)
    - 발급방식(다운로드, 난수쿠폰.. 등등)
    - 유효 기간
    - 사용 상태
    등은 언제나 필요
    """
    id: UUID
    code: str
    name: str
    discount_policy: DiscountPolicy    # TODO! 내부적으로 policy 위임
    valid_until: datetime
    status: str                      # TODO! 쿠폰 상태 추가
    created_at: datetime
    updated_at: datetime
    target_product_code: Optional[str] = None
    target_user_id: Optional[UUID] = None
    minimum_purchase_amount: Decimal = Decimal("0")

    # def apply(self, price: Decimal) -> Decimal:
    #     if self.status != "AVAILABLE" or self.valid_until < datetime.now():
    #         raise ValueError("유효하지 않은 쿠폰")
    #     return self.discount_policy.apply(price)
