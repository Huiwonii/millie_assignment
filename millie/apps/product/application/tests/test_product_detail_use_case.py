from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from apps.product.application.product_detail_use_case import ProductDetailUseCase
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import (
    PercentageDiscountPolicy,
    FixedDiscountPolicy,
    DiscountPolicy,
)


class ProductDetailUseCaseTest(TestCase):
    def setUp(self):
        past_dt = timezone.now() - timedelta(days=10)
        future_dt = timezone.now() + timedelta(days=30)

        # 두 가지 상품
        self.product_entity_book1 = ProductEntity(
            code="BOOK001", name="테스트 도서 1", price=Decimal("5000.00"),
            status="ACTIVE", created_at=past_dt, updated_at=None,
        )
        self.product_entity_book2 = ProductEntity(
            code="BOOK002", name="테스트 도서 2", price=Decimal("22000.00"),
            status="ACTIVE", created_at=past_dt, updated_at=None,
        )

        # 정상 쿠폰 (ALL, 10% 할인, 최소 적용 15,000원)
        self.coupon_10_percent_for_all_products = CouponEntity(
            id="uuid-10percent",
            code="COUPON03",
            name="테스트 쿠폰 3",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=future_dt,
            status="ACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("15000.00"),
            is_active=True,
        )
        # 정상 쿠폰 (BOOK002 전용, 고정 5,000원 할인)
        self.coupon_5000_fixed_for_book002 = CouponEntity(
            id="uuid-5000fixed",
            code="COUPON02",
            name="테스트 쿠폰 2",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("5000")),
            valid_until=future_dt,
            status="ACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="PRODUCT",
            target_product_code="BOOK002",
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 만료된 쿠폰 (ALL, 10% 할인)
        expired_dt = timezone.now() - timedelta(days=1)
        self.coupon_expired = CouponEntity(
            id="uuid-expired",
            code="COUPON99",
            name="만료 쿠폰",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=expired_dt,
            status="ACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 비활성화된 쿠폰 (ALL, 10% 할인)
        self.coupon_inactive = CouponEntity(
            id="uuid-inactive",
            code="COUPON88",
            name="비활성 쿠폰",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=future_dt,
            status="INACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=False,
        )
        # 특정 사용자(“USER123”) 전용 쿠폰 (ALL, 20% 할인)
        self.coupon_for_user123 = CouponEntity(
            id="uuid-user",
            code="COUPON_USER123",
            name="사용자 전용 쿠폰",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.20")),
            valid_until=future_dt,
            status="ACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="USER",
            target_product_code=None,
            target_user_id="USER123",
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 최소 구매 금액 경계값 쿠폰 (ALL, 고정 1,000원 할인, 최소 적용 5,000원)
        self.coupon_min5000 = CouponEntity(
            id="uuid-min5000",
            code="COUPON_MIN5000",
            name="경계값 쿠폰",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("1000")),
            valid_until=future_dt,
            status="ACTIVE",
            created_at=past_dt,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("5000.00"),
            is_active=True,
        )

    def test_쿠폰없으면_정가반환(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=None
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_쿠폰한개적용시_할인(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_10_percent_for_all_products],
            get_coupons_by_code=lambda codes: [self.coupon_10_percent_for_all_products],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[self.coupon_10_percent_for_all_products.code]
        )
        self.assertEqual(price_result.discounted, Decimal("19800.00"))

    def test_쿠폰여러개_누적적용시_우선순위에_따라_할인(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [
                self.coupon_10_percent_for_all_products,
                self.coupon_5000_fixed_for_book002
            ],
            get_coupons_by_code=lambda codes: [
                self.coupon_10_percent_for_all_products,
                self.coupon_5000_fixed_for_book002
            ],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[self.coupon_10_percent_for_all_products.code,
                         self.coupon_5000_fixed_for_book002.code]
        )
        self.assertEqual(price_result.discounted, Decimal("14800.00"))

    def test_최소적용금액_안되는상품에_쿠폰적용시도(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book1)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_10_percent_for_all_products],
            get_coupons_by_code=lambda codes: [self.coupon_10_percent_for_all_products],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book1.code,
            user=None,
            coupon_code=[self.coupon_10_percent_for_all_products.code],
        )
        self.assertEqual(price_result.discounted, Decimal("5000.00"))

    def test_만료된_쿠폰적용시도(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_expired],
            get_coupons_by_code=lambda codes: [self.coupon_expired],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[self.coupon_expired.code],
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_없는_쿠폰적용시도(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=["INVALID_COUPON"],
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_사용할_수_없는_상태의_쿠폰적용시도(self):
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_inactive],
            get_coupons_by_code=lambda codes: [self.coupon_inactive],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[self.coupon_inactive.code],
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_상품대상불일치_쿠폰적용시도(self):
        # 상품 BOOK001 전용 쿠폰을 BOOK002에 적용 시도
        coupon_book1_only = CouponEntity(
            id="uuid-book1only",
            code="COUPON_BOOK1",
            name="BOOK001 전용 고정 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("3000")),
            valid_until=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
            target_type="PRODUCT",
            target_product_code="BOOK001",
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_book1_only],
            get_coupons_by_code=lambda codes: [coupon_book1_only],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[coupon_book1_only.code],
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_사용자대상불일치_쿠폰적용시도(self):
        # USER123 전용 쿠폰을 OTHER_USER가 사용 시도
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_for_user123],
            get_coupons_by_code=lambda codes: [self.coupon_for_user123],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        # user 파라미터에 "OTHER_USER"를 넣어 테스트
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user="OTHER_USER",
            coupon_code=[self.coupon_for_user123.code],
        )
        self.assertEqual(price_result.discounted, Decimal("22000.00"))

    def test_최소적용금액_경계값_쿠폰적용(self):
        # BOOK001 가격 5,000원, 최소 적용 금액 5,000원인 쿠폰(1000원 할인) 적용 시
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book1)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_min5000],
            get_coupons_by_code=lambda codes: [self.coupon_min5000],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book1.code,
            user=None,
            coupon_code=[self.coupon_min5000.code],
        )
        # 5,000원 → 1,000원 할인 → 4,000원
        self.assertEqual(price_result.discounted, Decimal("4000.00"))

    def test_쿠폰순서에_따른_할인차이(self):
        # BOOK002 가격 20,000원으로 가정
        book = ProductEntity(
            code="BOOK003",
            name="테스트 도서 3",
            price=Decimal("20000.00"),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
        )
        # 쿠폰 A: 10% 할인, B: 고정 5,000원 할인
        coupon_pct = CouponEntity(
            id="uuid-order1",
            code="COUPON_PCT",
            name="20% 할인 쿠폰",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.20")),
            valid_until=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        coupon_fix = CouponEntity(
            id="uuid-order2",
            code="COUPON_FIX",
            name="고정 5,000원 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("5000")),
            valid_until=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # (1) [pct, fix]: 20,000 → 16,000 → 11,000
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: book)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )

        mock_coupon_service1 = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_pct, coupon_fix],
            get_coupons_by_code=lambda codes: [coupon_pct, coupon_fix],
        )
        use_case1 = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service1,
        )
        _, _, result1 = use_case1.execute(
            code=book.code,
            user=None,
            coupon_code=[coupon_pct.code, coupon_fix.code],
        )
        self.assertEqual(result1.discounted, Decimal("11000.00"))

        # (2) [fix, pct]: 20,000 → 15,000 → 12,000
        mock_coupon_service2 = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_fix, coupon_pct],
            get_coupons_by_code=lambda codes: [coupon_fix, coupon_pct],
        )
        use_case2 = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service2,
        )
        _, _, result2 = use_case2.execute(
            code=book.code,
            user=None,
            coupon_code=[coupon_fix.code, coupon_pct.code],
        )
        self.assertEqual(result2.discounted, Decimal("12000.00"))

    def test_할인서비스_예외발생(self):
        # DiscountPolicyStrategy.apply()가 예외를 던질 때 전파되는지 확인
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        # CouponService 정상 쿠폰 반환
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_5000_fixed_for_book002],
            get_coupons_by_code=lambda codes: [self.coupon_5000_fixed_for_book002],
        )
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )

        # DiscountService가 실제로는 사용되지 않으므로 Mock
        # to_discount_policy()는 FixedDiscountPolicy 객체이고, apply()를 patch
        broken_policy = mock.Mock(spec=DiscountPolicy)
        broken_policy.apply.side_effect = Exception("할인 실패")
        # 쿠폰 도메인 객체의 to_discount_policy()를 강제로 broken_policy 리턴하게 만듬
        self.coupon_5000_fixed_for_book002.to_discount_policy = lambda: broken_policy

        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        with self.assertRaises(Exception) as cm:
            use_case.execute(
                code=self.product_entity_book2.code,
                user=None,
                coupon_code=[self.coupon_5000_fixed_for_book002.code],
            )
        self.assertIn("할인 실패", str(cm.exception))

    def test_중복_쿠폰코드_적용시도(self):
        # 동일 쿠폰 코드를 중복 전달하면 한 번만 적용(중복 방지) 혹은 두 번 적용되는지 확인
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: self.product_entity_book2)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )
        # 두 번 동일 쿠폰 반환
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_5000_fixed_for_book002, self.coupon_5000_fixed_for_book002],
            get_coupons_by_code=lambda codes: [self.coupon_5000_fixed_for_book002, self.coupon_5000_fixed_for_book002],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=self.product_entity_book2.code,
            user=None,
            coupon_code=[self.coupon_5000_fixed_for_book002.code, self.coupon_5000_fixed_for_book002.code],
        )
        # 쿠폰을 두 번 적용했다면 22,000 - 5,000 - 5,000 = 12,000
        self.assertEqual(price_result.discounted, Decimal("12000.00"))

    def test_음수_최종가격_방어(self):
        # 상품 가격 4,000원, 고정 5,000원 쿠폰 적용시 음수가 되면 0으로 방어
        cheap_book = ProductEntity(
            code="BOOK004",
            name="저가 도서",
            price=Decimal("4000.00"),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
        )
        coupon_over = CouponEntity(
            id="uuid-over",
            code="COUPON_OVER",
            name="과도한 할인 쿠폰",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("5000")),
            valid_until=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        mock_product_repo = mock.Mock(get_product_by_code=lambda code: cheap_book)
        mock_promotion_service = mock.Mock()
        mock_promotion_service.apply_policy.side_effect = lambda product_code, original_price, user=None: PriceResultEntity(
            original=original_price,
            discounted=original_price,
            discount_amount=Decimal("0.00"),
            discount_types=[]
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_over],
            get_coupons_by_code=lambda codes: [coupon_over],
        )
        use_case = ProductDetailUseCase(
            product_repo=mock_product_repo,
            promotion_service=mock_promotion_service,
            coupon_service=mock_coupon_service,
        )
        _, _, price_result = use_case.execute(
            code=cheap_book.code,
            user=None,
            coupon_code=[coupon_over.code],
        )
        # 최종 금액이 음수가 되면 0으로 방어
        self.assertEqual(price_result.discounted, Decimal("0.00"))
