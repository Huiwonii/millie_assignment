from abc import (
    ABC,
    abstractmethod,
)
from uuid import UUID
from typing import Optional
from apps.pricing.domain.entity import Coupon
from apps.pricing.domain.discount_policy import DiscountPolicy


class CouponRepository(ABC):
    @abstractmethod
    def get_coupon_by_code(
        self,
        coupon_code: UUID,
    ) -> Optional[Coupon]:
        """
        주어진 쿠폰 코드에 해당하는 쿠폰 도메인 객체를 반환
        쿠폰이 없거나 만료된 경우 None을 반환
        """
        pass

    @abstractmethod
    def get_discount_policy_by_code(
        self,
        target_product_code: str,
    ) -> Optional[DiscountPolicy]:
        """
        주어진 할인 정책 코드에 해당하는 할인 정책 도메인 객체를 반환
        할인 정책이 없거나 만료된 경우 None을 반환
        """

        