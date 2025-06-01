# from decimal import Decimal


# class PriceResult:
#     def __init__(
#         self,
#         original: Decimal,
#         discounted: Decimal,
#         discount_amount: Decimal = Decimal("0"),
#         discount_type: str = None,
#     ):
#         self.original = original
#         self.discounted = discounted
#         self.discount_amount = discount_amount
#         self.discount_type = discount_type



from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class PriceResult:
    original: Decimal
    discounted: Decimal
    discount_amount: Decimal = Decimal("0")
    discount_type: Optional[str] = None