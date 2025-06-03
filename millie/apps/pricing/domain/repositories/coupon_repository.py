from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from typing import (
    List,
    Optional,
)
from uuid import UUID

from apps.pricing.domain.entity.coupon import Coupon


class CouponRepository(ABC):

    @abstractmethod
    def get_coupons_by_code(
        self,
        coupon_code: List[str],
        is_valid: bool = True,
    ) -> List[Optional[Coupon]]:
        pass


    @abstractmethod
    def list_active_not_expired(self, reference_time: datetime) -> List[Coupon]:
        pass