from typing import List
from apps.product.domain.repository import ProductRepository
from apps.product.domain.entity import Product as ProductDomainEntity


class ProductListUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
    ) -> None:
        self.product_repo = product_repo

    def execute(self) -> List[ProductDomainEntity]:
        return self.product_repo.get_products()


    def validate(self) -> None:
        pass


class ProductDetailUseCase:
    def __init__(self, product_repo: ProductRepository) -> None:
        self.product_repo = product_repo

    def execute(self, code: str) -> ProductDomainEntity:
        return self.product_repo.get_product(code)

    def validate(self, code: str) -> None:
        if not code:
            raise ValueError("Code is required")