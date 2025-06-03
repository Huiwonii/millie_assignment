from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status

from apps.product.infrastructure.persistence.models import (
    Book as BookModel,
    BookDetail as BookDetailModel,
    BookFeature as BookFeatureModel,
    PublishInfo as PublishInfoModel,
    Author as AuthorModel,
)
from apps.product.domain.value_objects import ProductStatus, VisibilityStatus
from apps.utils import messages, const


class ProductDetailAPITest(APITestCase):
    def setUp(self):
        now = timezone.now()

        # ── ACTIVE 상태의 Book 생성 ───────────────────────────────────────────
        self.book = BookModel.objects.create(
            code="BOOK001",
            name="Test Book",
            price=Decimal("15000.00"),
            status=ProductStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )

        # ── BookDetail 생성 ───────────────────────────────────────────────────
        BookDetailModel.objects.create(
            book_code=self.book,
            category="FICTION",
            description="이것은 테스트 도서 1의 설명입니다.",
            status=VisibilityStatus.VISIBLE.value,
            created_at=now,
            updated_at=now,
        )

        # ── Feature 생성 ──────────────────────────────────────────────────────
        BookFeatureModel.objects.create(
            book_code=self.book,
            feature="Feature Type 1",
            status=VisibilityStatus.VISIBLE.value,
            created_at=now,
            updated_at=now,
        )

        # ── PublishInfo 생성 ──────────────────────────────────────────────────
        PublishInfoModel.objects.create(
            book_code=self.book,
            publisher="TestPub",
            published_date=now.date(),
            status=VisibilityStatus.VISIBLE.value,
            created_at=now,
            updated_at=now,
        )

        # ── Author 생성 ───────────────────────────────────────────────────────
        AuthorModel.objects.create(
            book_code=self.book,
            author="Author1",
            status=VisibilityStatus.VISIBLE.value,
            created_at=now,
            updated_at=now,
        )

        # ── INACTIVE 상태의 Book 생성 ───────────────────────────────────────────
        BookModel.objects.create(
            code="BOOK002",
            name="Inactive Book",
            price=Decimal("10000.00"),
            status=ProductStatus.SOLD_OUT.value,
            created_at=now,
            updated_at=now,
        )

    def test_product_detail_without_coupon(self):
        """
        ACTIVE 상태의 상품 조회 시,
        → 200 OK
        → data 내에 product, available_discount keys 존재
        → product.price, product.code, product.name 일치
        → available_discount는 빈 리스트
        """
        url = reverse("product-detail", args=[self.book.code])
        response = self.client.get(url)

        # 1) HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2) 응답 구조 확인
        self.assertEqual(response.data["code"], status.HTTP_200_OK)
        self.assertEqual(response.data["message"], messages.OK)
        data = response.data["data"]

        # 3) "product" 필드
        product = data["product"]
        self.assertEqual(product["code"], self.book.code)
        self.assertEqual(product["name"], self.book.name)
        self.assertEqual(product["price"], "15000.00")

        # 4) "available_discount"는 빈 리스트
        self.assertIn(const.AVAILABLE_DISCOUNT, data)
        self.assertIsInstance(data[const.AVAILABLE_DISCOUNT], list)
        self.assertEqual(len(data[const.AVAILABLE_DISCOUNT]), 0)

    def test_product_detail_not_found(self):
        """
        존재하지 않는 상품 코드 조회 → 404 Not Found
        """
        url = reverse("product-detail", args=["NON_EXISTENT"])
        response = self.client.get(url)

        # 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], status.HTTP_404_NOT_FOUND)
        self.assertIn("없거나 판매 불가", response.data["message"])
        self.assertEqual(response.data["data"], {})

    def test_product_detail_inactive(self):
        """
        INACTIVE 상태의 상품 조회 → 404 Not Found
        """
        url = reverse("product-detail", args=["BOOK002"])
        response = self.client.get(url)

        # 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], status.HTTP_404_NOT_FOUND)
        self.assertIn("없거나 판매 불가", response.data["message"])
        self.assertEqual(response.data["data"], {})

    def test_product_detail_nested_relations(self):
        """
        ACTIVE 상태의 상품 조회 시, nested한 detail/feature/publish_info/author 정보가 응답에 포함되는지 확인
        """
        url = reverse("product-detail", args=[self.book.code])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        product = data["product"]

        # 1) detail 객체 검증
        self.assertIn("detail", product)
        detail = product["detail"]
        self.assertEqual(detail["category"], "FICTION")
        self.assertEqual(detail["description"], "이것은 테스트 도서 1의 설명입니다.")
        self.assertEqual(detail["status"], VisibilityStatus.VISIBLE.value)
        self.assertIn("created_at", detail)
        self.assertIn("updated_at", detail)

        # 2) feature 객체 검증
        self.assertIn("feature", product)
        feature = product["feature"]
        self.assertEqual(feature["feature"], "Feature Type 1")
        self.assertEqual(feature["status"], VisibilityStatus.VISIBLE.value)
        self.assertIn("created_at", feature)
        self.assertIn("updated_at", feature)

        # 3) publish_info 객체 검증
        self.assertIn("publish_info", product)
        publish_info = product["publish_info"]
        self.assertEqual(publish_info["publisher"], "TestPub")
        self.assertTrue(isinstance(publish_info["published_date"], str))
        self.assertEqual(publish_info["status"], VisibilityStatus.VISIBLE.value)
        self.assertIn("created_at", publish_info)
        self.assertIn("updated_at", publish_info)

        # 4) author 객체 검증
        self.assertIn("author", product)
        author = product["author"]
        self.assertEqual(author["author"], "Author1")
        self.assertEqual(author["status"], VisibilityStatus.VISIBLE.value)
        self.assertIn("created_at", author)
        self.assertIn("updated_at", author)

    def test_additional_product_info_fields(self):
        """
        응답의 product 안에 'created_at'/'updated_at'이 ISO 8601 포맷 문자열로 들어가는지 확인
        """
        url = reverse("product-detail", args=[self.book.code])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data["data"]["product"]

        # created_at, updated_at 필드가 문자열로 존재
        self.assertIn("created_at", product)
        self.assertIn("updated_at", product)
        self.assertTrue(isinstance(product["created_at"], str))
        self.assertTrue(isinstance(product["updated_at"], str))
