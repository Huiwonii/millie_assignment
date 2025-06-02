# apps/product/interface/tests/test_product_detail_api.py

import uuid
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status

from apps.product.infrastructure.persistence.models import (
    Book as BookModel,
    Author as AuthorModel,
    PublishInfo as PublishInfoModel,
)
from apps.product.domain.value_objects import ProductStatus, VisibilityStatus
from apps.utils import messages, const


class ProductDetailAPITest(APITestCase):
    def setUp(self):
        # ACTIVE 상태의 Book 모델 생성
        self.book = BookModel.objects.create(
            code="BOOK001",
            name="Test Book",
            price=Decimal("15000.00"),
            status=ProductStatus.ACTIVE.value,
        )
        # Author, PublishInfo
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

        BookModel.objects.create(
            code="BOOK002",
            name="Inactive Book",
            price=Decimal("10000.00"),
            status=ProductStatus.SOLD_OUT.value,
        )

    def test_product_detail_without_coupon(self):
        """
        ACTIVE 상태의 상품 조회, coupon_code 파라미터 없을 때
        → 200 OK
        → "data" 내에 "product", "available_discount", "price_calculate_result" 키 존재
          * available_discount은 빈 리스트
          * price_calculate_result: original == discounted == price, discount_amount == 0
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

        # 5) "price_calculate_result"
        price_result = data["price_calculate_result"]
        self.assertEqual(price_result["original"], "15000.00")
        self.assertEqual(price_result["discounted"], "15000.00")
        self.assertEqual(price_result["discount_amount"], "0.00")
        # discount_type은 None으로 직렬화될 수 있음
        self.assertTrue(price_result.get("discount_type") in (None, "", "null"))

    def test_product_detail_not_found(self):
        """
        존재하지 않는 상품 코드 조회 → NotFoundError로 404 Not Found
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

    def test_product_detail_with_invalid_coupon_code(self):
        """
        ACTIVE 상품에 잘못된 coupon_code 넘겨도 200 OK,
        available_discount은 빈 리스트,
        price_calculate_result는 원가 그대로
        """
        url = reverse("product-detail", args=[self.book.code])
        # 잘못된 쿠폰 코드 전달
        response = self.client.get(f"{url}?{const.COUPON_CODE}=INVALID")

        # 1) HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], status.HTTP_200_OK)

        data = response.data["data"]

        # 2) available_discount은 빈 리스트
        self.assertEqual(data[const.AVAILABLE_DISCOUNT], [])

        # 3) 가격은 변동 없음
        price_result = data["price_calculate_result"]
        self.assertEqual(price_result["original"], "15000.00")
        self.assertEqual(price_result["discounted"], "15000.00")
        self.assertEqual(price_result["discount_amount"], "0.00")

    def test_product_detail_with_valid_coupon(self):
        """
        ACTIVE 상품에 유효한 쿠폰 생성 후 coupon_code로 넘기면,
        available_discount에 해당 쿠폰 포함,
        price_calculate_result가 올바르게 할인된 것을 검증
        """
        from apps.pricing.infrastructure.persistence.models import (
            DiscountPolicy as DiscountPolicyModel,
            DiscountTarget as DiscountTargetModel,
            Coupon as CouponModel,
        )
        from apps.pricing.domain.value_objects import TargetType, DiscountType

        # 1) 할인 정책 생성: 10% 할인
        dp_id = uuid.uuid4()
        discount_policy = DiscountPolicyModel.objects.create(
            id=dp_id,
            discount_type=DiscountType.PERCENTAGE.value,
            value=Decimal("0.10"),        # 10%
            target_type=TargetType.ALL.value,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
            effective_start_at=timezone.now() - timezone.timedelta(days=1),
            effective_end_at=timezone.now() + timezone.timedelta(days=30),
        )

        # 2) 쿠폰 생성: BOOK001 상품 대상 ALL
        cp_id = uuid.uuid4()
        coupon = CouponModel.objects.create(
            id=cp_id,
            code="COUPON10",
            name="10% 할인 쿠폰",
            valid_until=timezone.now() + timezone.timedelta(days=10),
            status="ACTIVE",
            discount_policy=discount_policy,
        )

        # 3) DiscountTarget 생성 (ALL 대상)
        DiscountTargetModel.objects.create(
            id=uuid.uuid4(),
            discount_policy=discount_policy,
            target_product_code=None,
            apply_priority=1,
        )

        # 4) 요청 시 coupon_code=COUPON10 전달
        url = reverse("product-detail", args=[self.book.code])
        response = self.client.get(f"{url}?{const.COUPON_CODE}=COUPON10")

        # 5) HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], status.HTTP_200_OK)

        data = response.data["data"]

        # 6) available_discount에 쿠폰 하나 포함
        discounts = data[const.AVAILABLE_DISCOUNT]
        self.assertIsInstance(discounts, list)
        self.assertEqual(len(discounts), 1)
        self.assertEqual(discounts[0]["code"], "COUPON10")

        # 7) price_calculate_result에서 10% 할인 적용
        price_result = data["price_calculate_result"]
        self.assertEqual(price_result["original"], "15000.00")
        # 15,000 × 0.9 = 13,500.00
        self.assertEqual(price_result["discounted"], "13500.00")
        self.assertEqual(price_result["discount_amount"], "1500.00")

    def test_product_detail_coupon_minimum_amount(self):
        """
        쿠폰 최소 구매 금액 조건 검사:
        Book 가격(15,000원)이 쿠폰 minimum_purchase_amount(20,000원)보다 낮으면,
        할인 적용 없이 반환
        """
        from apps.pricing.infrastructure.persistence.models import (
            DiscountPolicy as DiscountPolicyModel,
            DiscountTarget as DiscountTargetModel,
            Coupon as CouponModel,
        )
        from apps.pricing.domain.value_objects import TargetType, DiscountType

        # 1) 할인 정책 생성: 고정 5,000원 할인, 최소 구매 금액 20,000원
        dp_id = uuid.uuid4()
        discount_policy = DiscountPolicyModel.objects.create(
            id=dp_id,
            discount_type=DiscountType.FIXED.value,
            value=Decimal("5000"),         # 5,000원 할인
            target_type=TargetType.ALL.value,
            minimum_purchase_amount=Decimal("20000.00"),
            is_active=True,
            effective_start_at=timezone.now() - timezone.timedelta(days=1),
            effective_end_at=timezone.now() + timezone.timedelta(days=30),
        )

        cp_id = uuid.uuid4()
        coupon = CouponModel.objects.create(
            id=cp_id,
            code="COUPON5K",
            name="5,000원 할인 쿠폰",
            valid_until=timezone.now() + timezone.timedelta(days=10),
            status="ACTIVE",
            discount_policy=discount_policy,
        )

        DiscountTargetModel.objects.create(
            id=uuid.uuid4(),
            discount_policy=discount_policy,
            target_product_code=None,
            apply_priority=1,
        )

        # 2) Book 가격: 15,000원 < 최소구매 20,000원 → 할인 적용 안 됨
        url = reverse("product-detail", args=[self.book.code])
        response = self.client.get(f"{url}?{const.COUPON_CODE}=COUPON5K")

        # 3) HTTP 200 OK (적용 가능한 쿠폰이 없으므로 정상 반환)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], status.HTTP_200_OK)

        data = response.data["data"]
        # 적용 가능한 쿠폰이 없으므로 빈 리스트
        self.assertEqual(data[const.AVAILABLE_DISCOUNT], [])

        price_result = data["price_calculate_result"]
        self.assertEqual(price_result["original"], "15000.00")
        self.assertEqual(price_result["discounted"], "15000.00")
        self.assertEqual(price_result["discount_amount"], "0.00")
