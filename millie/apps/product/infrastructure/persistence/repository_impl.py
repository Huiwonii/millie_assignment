from typing import (
    List,
    Optional,
)
from apps.product.domain.repository import ProductRepository
from apps.product.domain.entity import Product as ProductDomainEntity
from apps.product.domain.value_objects import ProductStatus
from apps.product.infrastructure.persistence.models import Book as BookModel
from apps.product.infrastructure.persistence.mapper import ProductMapper


class ProductRepositoryImpl(ProductRepository):

    def __init__(self):
        self.mapper = ProductMapper()

    def get_products(
        self,
        code: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[ProductDomainEntity]:
        qs = (
            BookModel.objects.select_related(
                "detail", "author", "publish_info"
            )
            .prefetch_related("feature") # feature는 still ManyToOne
            .all()
        )
        if code:
            qs = qs.filter(code=code)

        if name:
            qs = qs.filter(name=name)

        qs = qs.filter(status=ProductStatus.ACTIVE.value)

        return [self.mapper.to_domain(book) for book in qs]


    def get_product_by_code(
        self,
        code: str,
    ) -> ProductDomainEntity:
        qs = (
            BookModel.objects.select_related(
                "detail", "author", "publish_info"
            )
            .prefetch_related("feature")
            .filter(code=code)
        )

        if not qs.exists():
            raise BookModel.DoesNotExist(f"Product with code {code} not found")

        return self.mapper.to_domain(qs.first())
