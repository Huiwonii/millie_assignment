from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
    Optional,
)
from uuid import UUID

from apps.pricing.domain.policy.discount_policy import DiscountPolicy


class PromotionRepository(ABC):

    @abstractmethod
    def get_active_promotions(
        self,
        target_product_code: Optional[str] = None,
        target_user_id: Optional[UUID] = None,
    ) -> List[DiscountPolicy]:

        pass
