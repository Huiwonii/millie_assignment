from typing import List
from uuid import UUID
from apps.product.domain.repository import ProductRepository
from apps.pricing.application.discount_service import DiscountService
from apps.product.domain.entity import Product as ProductDomainEntity
from apps.pricing.domain.entity.price_result import PriceResult


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
    def __init__(
        self,
        product_repo: ProductRepository,
        discount_service: DiscountService,
    ) -> None:
        self.product_repo = product_repo
        self.discount_service = discount_service

    def execute(
        self,
        code: str,
        coupon_code: UUID = None,
    ) -> PriceResult:

        product = self.product_repo.get_product_by_code(code)

        if not product:
            raise ValueError("Product not found")

        return self.discount_service.apply_best_policy(
            product_code=product.code,
            original_price=product.price,
        )

    def validate(self, code: str) -> None:
        if not code:
            raise ValueError("Code is required")