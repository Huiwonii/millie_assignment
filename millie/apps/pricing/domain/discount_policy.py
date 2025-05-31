from abc import ABC, abstractmethod
from decimal import Decimal
from dataclasses import dataclass




class PriceResult:  # TODO! 이 친구의 역할..?
    def __init__(
        self,
        original: Decimal,
        discounted: Decimal,
        discount_amount: Decimal,
        discount_type: str,
    ):
        self.original = original
        self.discounted = discounted
        self.discount_amount = discount_amount
        self.discount_type = discount_type


class DiscountPolicy(ABC):
    @abstractmethod
    def apply(self, price: Decimal) -> 'PriceResult':
        pass


class PercentageDiscountPolicy(DiscountPolicy):

    def __init__(
        self,
        discount_type: str,
        discount_rate: Decimal,
        already_discounted_amount: Decimal = Decimal("0"),
    ):
        if not (Decimal("0") <= discount_rate <= Decimal("1")):
            raise ValueError("할인율은 0 이상 1 이하의 값이어야 합니다.")

        self._discount_type = discount_type
        self._discount_rate = discount_rate
        self._already_discounted_amount = already_discounted_amount

    def apply(
        self,
        original_price: Decimal,
    ) -> PriceResult:
        discount_amount = (original_price * self._discount_rate) + self._already_discounted_amount
        final_price = original_price - discount_amount

        return PriceResult(
            original=original_price,
            discounted=final_price,
            discount_amount=discount_amount,
            discount_type=self._discount_type,
        )


class FixedDiscountPolicy(DiscountPolicy):

    def __init__(
        self,
        discount_type: str,
        discount_amount: Decimal,
        already_discounted_amount: Decimal = Decimal("0"),
    ):
        if discount_amount < Decimal("0"):
            raise ValueError("할인 금액은 0 이상이어야 합니다.")

        self._discount_type = discount_type
        self._discount_amount = discount_amount
        self._already_discounted_amount = already_discounted_amount

    def apply(
        self,
        original_price: Decimal,
    ) -> PriceResult:

        discount_amount = min((self._discount_amount + self._already_discounted_amount), original_price)
        final_price = original_price - discount_amount

        return PriceResult(
            original=original_price,
            discounted=final_price,
            discount_amount=discount_amount,
            discount_type=self._discount_type,
        )
