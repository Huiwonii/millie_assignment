from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.product.domain.value_objects import (
    ProductStatus,
    VisibilityStatus,
)
from apps.product.infrastructure.persistence.models import (
    Book as BookModel,
    Author as AuthorModel,
    PublishInfo as PublishInfoModel,
)
from apps.utils import messages


class ProductListAPITest(APITestCase):
    def setUp(self):
        # 1) ACTIVE 상태의 Book 모델 인스턴스 생성
        self.book = BookModel.objects.create(
            code="BOOK001",
            name="Test Book",
            price=Decimal("10000.00"),
            status=ProductStatus.ACTIVE.value,
        )
        # Author, PublishInfo 연관 객체 생성
        AuthorModel.objects.create(
            book_code=self.book,
            author="Author1",
            status=VisibilityStatus.VISIBLE.value,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        PublishInfoModel.objects.create(
            book_code=self.book,
            publisher="TestPub",
            published_date=timezone.now().date(),
            status=VisibilityStatus.VISIBLE.value,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        # 품절된 상품 추가(리스트에 나오면 안됨)
        BookModel.objects.create(
            code="BOOK002",
            name="Inactive Book",
            price=Decimal("5000.00"),
            status=ProductStatus.SOLD_OUT.value,
        )

    def test_product_list_returns_active_products(self):
        """
        GET /api/v1/products 호출 시,
        ACTIVE 상태의 상품만 반환되고,
        필드(code, name, price, author, publisher, published_date 등)가 올바르게 직렬화되어야 한다.
        """
        url = reverse("product-list")

        # 1) 파라미터 없이 호출
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], status.HTTP_200_OK)
        self.assertEqual(response.data["message"], messages.OK)
        data = response.data["data"]
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        item = data[0]
        self.assertEqual(item["code"], "BOOK001")
        self.assertEqual(item["name"], "Test Book")
        self.assertEqual(item["price"], "10000.00")
        self.assertEqual(item["author"], "Author1")
        self.assertEqual(item["publisher"], "TestPub")
        self.assertIsInstance(item["published_date"], str)

        # 2) 허용되지 않은 쿼리 파라미터(foo=bar)가 있어도 동일하게 동작해야 한다
        response_with_extra = self.client.get(f"{url}?foo=bar")
        self.assertEqual(response_with_extra.status_code, status.HTTP_200_OK)
        self.assertEqual(response_with_extra.data["data"][0]["code"], "BOOK001")

    def test_empty_product_list(self):
        """
        데이터베이스에 ACTIVE 상태 상품이 하나도 없을 때,
        GET /api/v1/products → data가 빈 리스트([])로 반환되어야 한다.
        """
        # 모든 상품을 INACTIVE로 업데이트하여 ACTIVE 상품이 없도록 만듦
        BookModel.objects.all().update(status=ProductStatus.DISCONTINUED.value)

        url = reverse("product-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], messages.NOT_FOUND)
        self.assertEqual(response.data["data"], [])
