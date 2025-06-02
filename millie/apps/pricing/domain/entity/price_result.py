from dataclasses import (
    dataclass,
    field,
)
from decimal import Decimal
from typing import (
    List,
    Optional,
)


@dataclass
class PriceResult:
    original: Decimal
    discounted: Decimal
    discount_amount: Decimal = Decimal("0")
    discount_types: List[str] = field(default_factory=list)