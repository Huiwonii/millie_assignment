from typing import List
from uuid import UUID
from apps.product.domain.repository import ProductRepository
from apps.product.domain.entity import Product as ProductEntity


class ProductListUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
    ) -> None:
        self.product_repo = product_repo

    def execute(self) -> List[ProductEntity]:
        return self.product_repo.get_products()

    def validate(self) -> None:
        pass

