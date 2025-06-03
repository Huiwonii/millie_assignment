from typing import (
    List,
    Optional,
)

from apps.product.domain.entity import Product as ProductEntity
from apps.product.domain.repository import ProductRepository
from apps.product.domain.value_objects import ProductStatus
from apps.product.infrastructure.persistence.mapper import ProductMapper
from apps.product.infrastructure.persistence.models import Book as BookModel

from apps.utils.exceptions import NotFoundException


class ProductRepoImpl(ProductRepository):

    def __init__(self):
        self.mapper = ProductMapper()

    def get_products(
        self,
        code: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[ProductEntity]:
        qs = (
            BookModel.objects.select_related(
                "detail", "author", "publish_info"
            ).prefetch_related("feature")
            .all()
        )
        if code:
            qs = qs.filter(code=code)

        if name:
            qs = qs.filter(name=name)

        qs = qs.filter(status=ProductStatus.ACTIVE.value)

        return [self.mapper.to_domain(book) for book in qs]


    def get_product_by_code(self, code: str) -> ProductEntity:
        try:
            book = BookModel.objects.get(code=code, status=ProductStatus.ACTIVE.value)
        except BookModel.DoesNotExist:
            raise NotFoundException(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")
        return self.mapper.to_domain(book)