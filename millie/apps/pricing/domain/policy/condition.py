from abc import (
    ABC,
    abstractmethod,
)
from typing import Optional
from uuid import UUID
from decimal import Decimal


class DiscountCondition(ABC):

    @abstractmethod
    def is_satisfied(
        self,
        price: Decimal,
        product_code: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> bool:
        pass
