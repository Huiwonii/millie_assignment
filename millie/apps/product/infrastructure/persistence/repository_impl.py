from typing import (
    List,
    Optional,
)
from apps.product.domain.repository import ProductRepository
from apps.product.domain.entity import Product as ProductDomainEntity
from apps.product.infrastructure.persistence.models import Book as BookModel
from apps.product.infrastructure.persistence.mapper import ProductMapper

class ProductRepositoryImpl(ProductRepository):

    def __init__(self):
        self.mapper = ProductMapper()

    # TODO! 필터를 위한 파라메트를 이런식으로 넘기는게 맞는지 고민할것
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

        qs = qs.filter(status="ACTIVE") # TODO! 아것도 비즈니스 룰인지 아니면 단순히 orm의 영역인지 고민

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

        return self.mapper.to_domain(qs.first()) # TODO! 확인
