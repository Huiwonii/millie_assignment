from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
    Optional,
)
from apps.product.domain.entity import Product


class ProductRepository(ABC):
    @abstractmethod
    def get_products(self) -> List[Product]:
        pass

    @abstractmethod
    def get_product_by_code(
        self,
        code: str
    ) -> Optional[Product]:
        pass
