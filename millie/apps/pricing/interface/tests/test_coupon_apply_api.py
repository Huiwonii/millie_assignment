from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import PercentageDiscountPolicy
from apps.utils import (
    const,
    messages,
)
from apps.utils.exceptions import NotFoundException

PATCH_TARGET = "apps.pricing.interface.views.coupon_apply_views.CalculatePriceUseCase"


class ApplyCouponAPITest(APITestCase):
    def setUp(self):
        self.product_code = "BOOK001"
        self.url = reverse("apply-coupon", args=[self.product_code])
        now = timezone.now()
        future = now + timedelta(days=30)

        self.example_coupon = CouponEntity(
            id="c1",
            code="TEST10",
            name="테스트 10% 할인",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=future,
            status="ACTIVE",
            created_at=now,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        self.example_price_result = PriceResultEntity(
            original=Decimal("20000.00"),
            discounted=Decimal("18000.00"),
            discount_amount=Decimal("2000.00"),
            discount_types=["PERCENTAGE"],
        )

    @mock.patch(PATCH_TARGET)
    def test_bad_request_extra_params(self, mock_use_case_cls):
        payload = {
            const.COUPON_CODE: ["TEST10"],
            "unexpected_key": "value"
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.BAD_REQUEST, response.data["message"])
        self.assertEqual(response.data["data"], {})

    @mock.patch(PATCH_TARGET)
    def test_product_not_found_returns_404(self, mock_use_case_cls):
        """
        CalculatePriceUseCase.fetch()가 NotFoundException을 던지면 404를 반환해야 한다.
        """
        instance = mock_use_case_cls.return_value
        instance.fetch.side_effect = NotFoundException("상품을 찾을 수 없습니다.")

        payload = {const.COUPON_CODE: ["TEST10"]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], status.HTTP_404_NOT_FOUND)
        self.assertIn("상품을 찾을 수 없습니다.", response.data["message"])
        self.assertEqual(response.data["data"], {})

    @mock.patch(PATCH_TARGET)
    def test_validate_failure_returns_404(self, mock_use_case_cls):
        """
        CalculatePriceUseCase.validate()가 NotFoundException을 던지면 404를 반환해야 한다.
        """
        instance = mock_use_case_cls.return_value
        instance.fetch.return_value = mock.Mock()
        instance.validate.side_effect = NotFoundException("유효하지 않은 쿠폰입니다.")

        payload = {const.COUPON_CODE: ["INVALID"]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], status.HTTP_404_NOT_FOUND)

        self.assertIn("유효하지 않은 쿠폰입니다.", response.data["message"])
        self.assertEqual(response.data["data"], {})

    @mock.patch(PATCH_TARGET)
    def test_internal_error_returns_500(self, mock_use_case_cls):
        """
        CalculatePriceUseCase.execute()가 일반 Exception을 던지면 500을 반환해야 한다.
        """
        instance = mock_use_case_cls.return_value
        instance.fetch.return_value = mock.Mock()
        instance.validate.return_value = None
        instance.execute.side_effect = Exception("계산 중 오류 발생")

        payload = {const.COUPON_CODE: ["TEST10"]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["code"], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(messages.INTERNAL_SERVER_ERROR, response.data["message"])
        self.assertEqual(response.data["data"], {})

    @mock.patch(PATCH_TARGET)
    def test_successful_apply_returns_200(self, mock_use_case_cls):
        """
        fetch, validate, execute가 모두 성공하면 200을 반환하고, 직렬화된 결과가 와야 한다.
        """
        instance = mock_use_case_cls.return_value
        dummy_product = mock.Mock()
        instance.fetch.return_value = dummy_product
        instance.validate.return_value = None

        available_coupons = [self.example_coupon]
        applied_policies = ["TEST10_PROMO"]
        instance.execute.return_value = (available_coupons, applied_policies, self.example_price_result)

        payload = {const.COUPON_CODE: ["TEST10"]}
        response = self.client.post(self.url, payload, format="json")

        # 이제 200 OK가 와야 한다!
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], status.HTTP_200_OK)
        self.assertEqual(response.data["message"], messages.OK)

        data = response.data["data"]

        # price_result 직렬화 검증
        pr = data["price_result"]
        self.assertEqual(Decimal(pr["original"]), self.example_price_result.original)
        self.assertEqual(Decimal(pr["discounted"]), self.example_price_result.discounted)
        self.assertEqual(Decimal(pr["discount_amount"]), self.example_price_result.discount_amount)
        self.assertListEqual(pr["discount_types"], self.example_price_result.discount_types)

        # available_coupons 직렬화 검증
        coupons = data["available_coupons"]
        self.assertIsInstance(coupons, list)
        self.assertEqual(len(coupons), 1)
        self.assertEqual(coupons[0]["code"], self.example_coupon.code)
        self.assertEqual(coupons[0]["name"], self.example_coupon.name)
        self.assertEqual(coupons[0]["target_type"], self.example_coupon.target_type)

        # applied_pricing_policies 검증
        self.assertListEqual(data["applied_pricing_policies"], applied_policies)
