from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import (
    Optional,
)
from .value_objects import (
    Category,
    Feature,
    ProductStatus,
    VisibilityStatus,
)

@dataclass
class Product:  # aggregate root
    code: str
    name: str
    price: int
    discount_rate: Decimal
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    detail: Optional[BookDetail] = None
    feature: Optional[BookFeature] = None
    publish_info: Optional[PublishInfo] = None
    author: Optional[Author] = None

    @property
    def discount_price(self) -> Decimal:
        if self.discount_rate is None:
            return self.price
        return self.price * (Decimal("1.0") - self.discount_rate)

    def __post_init__(self):
        if self.status == ProductStatus.ACTIVE and not self.detail:
            raise ValueError  # TODO! 커스텀 에러 처리 화면에 보이는 활성상품의 경우 detail 정보 포함해야함


@dataclass(frozen=True)
class BookDetail:
    category: Category
    description: str
    status: VisibilityStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BookFeature:
    feature: Feature
    status: VisibilityStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PublishInfo:
    publisher: str
    published_date: datetime
    status: VisibilityStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Author:
    author: str
    status: VisibilityStatus
    created_at: datetime
    updated_at: datetime