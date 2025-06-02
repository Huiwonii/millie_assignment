from abc import (
    ABC,
    abstractmethod,
)
from decimal import Decimal
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity


class DiscountPolicy(ABC):
    @abstractmethod
    def apply(self, price: Decimal) -> PriceResultEntity:
        pass


class PercentageDiscountPolicy(DiscountPolicy):

    def __init__(
        self,
        discount_type: str,
        discount_rate: Decimal,
    ):
        if not (Decimal("0") <= discount_rate <= Decimal("1")):
            raise ValueError("할인율은 0 이상 1 이하의 값이어야 합니다.")

        self._discount_type = discount_type
        self._discount_rate = discount_rate

    def apply(
        self,
        original_price: Decimal,
    ) -> PriceResultEntity:
        discount_amount = (original_price * self._discount_rate)
        final_price = original_price - discount_amount

        return PriceResultEntity(
            original=original_price,
            discounted=final_price,
            discount_amount=discount_amount,
            discount_types=[self._discount_type],
        )

    @property
    def discount_type(self) -> str:
        return self._discount_type

    @property
    def value(self) -> Decimal:
        return self._discount_rate


class FixedDiscountPolicy(DiscountPolicy):

    def __init__(
        self,
        discount_type: str,
        discount_amount: Decimal,
    ):
        if discount_amount < Decimal("0"):
            raise ValueError("할인 금액은 0 이상이어야 합니다.")

        self._discount_type = discount_type
        self._discount_amount = discount_amount

    def apply(
        self,
        original_price: Decimal,
    ) -> PriceResultEntity:

        discount_amount = min(self._discount_amount, original_price)
        final_price = original_price - discount_amount

        return PriceResultEntity(
            original=original_price,
            discounted=final_price,
            discount_amount=discount_amount,
            discount_types=[self._discount_type],
        )

    @property
    def discount_type(self) -> str:
        return self._discount_type

    @property
    def value(self) -> Decimal:
        return self._discount_amount

