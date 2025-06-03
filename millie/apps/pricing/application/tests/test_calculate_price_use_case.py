from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from apps.pricing.application.use_case.calculate_price_use_case import CalculatePriceUseCase
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.policy.discount_policy import (
    PercentageDiscountPolicy,
    FixedDiscountPolicy,
)


class CalculatePriceUseCaseTest(TestCase):
    def setUp(self):
        now = timezone.now()
        past = now - timedelta(days=10)
        future = now + timedelta(days=30)

        # ── 상품 엔티티 두 개 준비 ─────────────────────────────────────────────
        self.book1 = ProductEntity(
            code="BOOK1",
            name="도서 1",
            price=Decimal("5000.00"),
            status="ACTIVE",
            created_at=past,
            updated_at=None,
        )
        self.book2 = ProductEntity(
            code="BOOK2",
            name="도서 2",
            price=Decimal("22000.00"),
            status="ACTIVE",
            created_at=past,
            updated_at=None,
        )

        # ── 쿠폰 엔티티들 준비 ───────────────────────────────────────────────
        # 1) 전체 대상 10% 할인, 최소 적용가 15000원, 만료 전
        self.coupon_all_10pct = CouponEntity(
            id="c1",
            code="ALL10",
            name="전체 10% 할인",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=future,
            status="ACTIVE",
            created_at=past,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("15000.00"),
            is_active=True,
        )
        # 2) BOOK2 전용 5000원 할인, 최소 적용가=0, 만료 전
        self.coupon_book2_5k = CouponEntity(
            id="c2",
            code="B2FIX5K",
            name="도서2 전용 5,000원 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("5000")),
            valid_until=future,
            status="ACTIVE",
            created_at=past,
            updated_at=None,
            target_type="PRODUCT",
            target_product_code="BOOK2",
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 3) 사용자 ABC 전용 20% 할인, 만료 전
        self.coupon_user_20pct = CouponEntity(
            id="c3",
            code="U20",
            name="사용자 ABC 전용 20% 할인",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.20")),
            valid_until=future,
            status="ACTIVE",
            created_at=past,
            updated_at=None,
            target_type="USER",
            target_product_code=None,
            target_user_id="ABC",
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 4) 최소 적용가 5000원, 1000원 할인 쿠폰, 만료 전
        self.coupon_min5k_1k = CouponEntity(
            id="c4",
            code="MIN5K1K",
            name="최소 5,000원 1,000원 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("1000")),
            valid_until=future,
            status="ACTIVE",
            created_at=past,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("5000.00"),
            is_active=True,
        )
        # 5) 만료된 쿠폰 (전체 10% 할인), 이미 expiry 날짜 지남
        expired_time = now - timedelta(days=1)
        self.coupon_expired = CouponEntity(
            id="c5",
            code="EXP10",
            name="만료 10% 할인",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=expired_time,
            status="ACTIVE",
            created_at=past,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )
        # 6) 비활성화 쿠폰 (전체 10% 할인)
        self.coupon_inactive = CouponEntity(
            id="c6",
            code="INACT10",
            name="비활성 10% 할인",
            discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
            valid_until=future,
            status="INACTIVE",
            created_at=past,
            updated_at=None,
            target_type="ALL",
            target_product_code=None,
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=False,
        )

        # ── 프로모션용 DiscountPolicy 두 개 준비 ─────────────────────────
        # PROMO1: BOOK2 최대 10% 할인 자동 적용, 우선순위 1
        self.promo_policy_book2 = PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10"))
        # PROMO2: 전체 대상 5% 할인(우선순위 2)
        self.promo_policy_all = PercentageDiscountPolicy("PERCENTAGE", Decimal("0.05"))

        # 테스트에서는 PromotionService.apply_policy(...)를 mock하여
        # (PriceResultEntity, has_promotion, promotion_name) 형태로 돌려줄 것.


    # ── 테스트 케이스 1: 프로모션만 적용 (쿠폰 없음) ───────────────────
    def test_프로모션만_적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.side_effect = lambda product_code, original_price, user=None: (
            PriceResultEntity(
                original=original_price,
                discounted=(original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_amount=(original_price - original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_types=["PERCENTAGE"]
            ),
            True,
            "BOOK2_10PERCENT_PROMO"
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=None,
        )

        self.assertEqual(len(available_coupons), 0)
        self.assertEqual(applied_coupons, ["BOOK2_10PERCENT_PROMO"])
        self.assertEqual(price_res.discounted, Decimal("19800.00"))
        self.assertEqual(price_res.discount_amount, Decimal("2200.00"))
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])


    # ── 테스트 케이스 2: 프로모션 후 쿠폰(책2 전용 5000원) 적용 ────────
    def test_프로모션후_쿠폰_적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.side_effect = lambda product_code, original_price, user=None: (
            PriceResultEntity(
                original=original_price,
                discounted=(original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_amount=(original_price - original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_types=["PERCENTAGE"]
            ),
            True,
            "BOOK2_10PERCENT_PROMO"
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_book2_5k],
            get_coupons_by_code=lambda codes: [self.coupon_book2_5k],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_book2_5k.code],
        )

        self.assertEqual(len(available_coupons), 1)
        self.assertIn("도서2 전용 5,000원 할인", applied_coupons)
        self.assertIn("BOOK2_10PERCENT_PROMO", applied_coupons)
        self.assertEqual(price_res.original, Decimal("22000.00"))
        self.assertEqual(price_res.discounted, Decimal("14800.00"))
        self.assertEqual(price_res.discount_amount, Decimal("7200.00"))
        self.assertIn("PERCENTAGE", price_res.discount_types)
        self.assertIn("FIXED", price_res.discount_types)


    # ── 테스트 케이스 3: 쿠폰만 적용 (프로모션 없음) ─────────────────
    def test_프로모션없고_쿠폰만적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_all_10pct],
            get_coupons_by_code=lambda codes: [self.coupon_all_10pct],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_all_10pct.code],
        )

        self.assertEqual(len(available_coupons), 1)
        self.assertEqual(applied_coupons, ["전체 10% 할인"])
        self.assertEqual(price_res.discounted, Decimal("19800.00"))
        self.assertEqual(price_res.discount_amount, Decimal("2200.00"))
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])


    # ── 테스트 케이스 4: 쿠폰 만료 시도 → 적용 안 되고 원가 ───────────────
    def test_만료된_쿠폰적용시도(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_expired],
            get_coupons_by_code=lambda codes: [self.coupon_expired],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_expired.code],
        )

        self.assertEqual(price_res.discounted, Decimal("22000.00"))
        self.assertEqual(applied_coupons, [])


    # ── 테스트 케이스 5: 최소 적용가 미만 쿠폰 시도 → 적용 안 되고 원가 ──────
    def test_최소금액미만_쿠폰적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book1)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("5000.00"),
                discounted=Decimal("5000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_min5k_1k],
            get_coupons_by_code=lambda codes: [self.coupon_min5k_1k],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book1,
            user=None,
            coupon_code=[self.coupon_min5k_1k.code],
        )

        self.assertEqual(price_res.discounted, Decimal("4000.00"))
        self.assertEqual(applied_coupons, ["최소 5,000원 1,000원 할인"])


    # ── 테스트 케이스 6: 사용자 전용 쿠폰 다른 사용자 시도 → 적용 안 되고 원가 ───
    def test_사용자전용쿠폰_다른사용자(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_user_20pct],
            get_coupons_by_code=lambda codes: [self.coupon_user_20pct],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user="XYZ",
            coupon_code=[self.coupon_user_20pct.code],
        )

        self.assertEqual(price_res.discounted, Decimal("22000.00"))
        self.assertEqual(applied_coupons, [])


    # ── 테스트 케이스 7: 쿠폰 상태가 INACTIVE → 적용 안 되고 원가 ───────────────
    def test_비활성쿠폰적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_inactive],
            get_coupons_by_code=lambda codes: [self.coupon_inactive],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_inactive.code],
        )

        self.assertEqual(price_res.discounted, Decimal("22000.00"))
        self.assertEqual(applied_coupons, [])


    # ── 테스트 케이스 8: 상품 대상 쿠폰 다른 상품 시도 → 적용 안 되고 원가 ───────
    def test_상품대상쿠폰_다른상품(self):
        coupon_book1_only = CouponEntity(
            id="c7",
            code="B1FIX2K",
            name="도서1 전용 2,000원 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("2000")),
            valid_until=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
            target_type="PRODUCT",
            target_product_code="BOOK1",
            target_user_id=None,
            minimum_purchase_amount=Decimal("0.00"),
            is_active=True,
        )

        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_book1_only],
            get_coupons_by_code=lambda codes: [coupon_book1_only],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[coupon_book1_only.code],
        )

        self.assertEqual(price_res.discounted, Decimal("22000.00"))
        self.assertEqual(applied_coupons, [])


    # ── 테스트 케이스 9: 쿠폰 중복 전달 → 2회 적용 ───────────────────────
    def test_중복쿠폰코드_전달(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_book2_5k, self.coupon_book2_5k],
            get_coupons_by_code=lambda codes: [self.coupon_book2_5k, self.coupon_book2_5k],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_book2_5k.code, self.coupon_book2_5k.code],
        )

        self.assertEqual(price_res.discounted, Decimal("12000.00"))
        self.assertEqual(
            applied_coupons,
            ["도서2 전용 5,000원 할인", "도서2 전용 5,000원 할인"]
        )


    # ── 테스트 케이스 10: 음수 최종 가격 방어 ───────────────────────────────
    def test_음수_최종가격_방어(self):
        cheap_book = ProductEntity(
            code="BOOK_CHEAP",
            name="저가책",
            price=Decimal("4000.00"),
            status="ACTIVE",
            created_at=timezone.now() - timedelta(days=10),
            updated_at=None,
        )
        coupon_over = CouponEntity(
            id="c8",
            code="OVERFIX10K",
            name="과도 10,000원 할인",
            discount_policy=FixedDiscountPolicy("FIXED", Decimal("10000")),
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

        mock_repo = mock.Mock(get_product_by_code=lambda code: cheap_book)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("4000.00"),
                discounted=Decimal("4000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_over],
            get_coupons_by_code=lambda codes: [coupon_over],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=cheap_book,
            user=None,
            coupon_code=[coupon_over.code],
        )

        self.assertEqual(price_res.discounted, Decimal("0.00"))
        self.assertEqual(applied_coupons, ["과도 10,000원 할인"])


    # ── 이하 추가된 테스트 케이스 11~20 ─────────────────────────────────────

    # 11) 사용자 전용 쿠폰을 올바른 사용자에게 적용 → 할인 적용
    def test_사용자전용쿠폰_정상유저(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_user_20pct],
            get_coupons_by_code=lambda codes: [self.coupon_user_20pct],
        )

        # coupon_user_20pct.is_available이 user=="ABC"일 때만 True를 반환하도록
        self.coupon_user_20pct.is_available = lambda user, product_code: (user == "ABC")
        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # user="ABC"로 전달 → coupon_user_20pct는 target_user_id="ABC"이므로 정상 적용
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user="ABC",
            coupon_code=[self.coupon_user_20pct.code],
        )

        # 22,000 * 0.8 = 17,600
        self.assertEqual(price_res.discounted, Decimal("17600.00"))
        self.assertEqual(applied_coupons, ["사용자 ABC 전용 20% 할인"])
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])


    # 12) 상품 대상 쿠폰을 올바른 상품에 적용 → 할인 적용
    def test_상품대상쿠폰_정상적용(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_book2_5k],
            get_coupons_by_code=lambda codes: [self.coupon_book2_5k],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_book2_5k.code],
        )

        self.assertEqual(price_res.discounted, Decimal("17000.00"))  # 22,000 - 5,000
        self.assertEqual(applied_coupons, ["도서2 전용 5,000원 할인"])
        self.assertListEqual(price_res.discount_types, ["FIXED"])


    # 13) 여러 “전체 대상” 쿠폰 순서에 따른 할인 차이 (percent → fixed)
    def test_전체쿠폰_여러개_적용_순서1(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        # get_applicable_coupons 리턴 순서는 coupon_all_10pct, coupon_min5k_1k
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_all_10pct, self.coupon_min5k_1k],
            get_coupons_by_code=lambda codes: [self.coupon_all_10pct, self.coupon_min5k_1k],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # (10% 먼저 → 19,800) → (19,800 - 1,000 = 18,800)
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_all_10pct.code, self.coupon_min5k_1k.code],
        )

        self.assertEqual(price_res.discounted, Decimal("18800.00"))
        self.assertEqual(
            applied_coupons,
            ["전체 10% 할인", "최소 5,000원 1,000원 할인"]
        )
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE", "FIXED"])


    # 14) 여러 “전체 대상” 쿠폰 순서에 따른 할인 차이 (fixed → percent)
    def test_전체쿠폰_여러개_적용_순서2(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_min5k_1k, self.coupon_all_10pct],
            get_coupons_by_code=lambda codes: [self.coupon_min5k_1k, self.coupon_all_10pct],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # (1,000원 먼저 → 21,000) → (21,000 *0.9 = 18,900)
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_min5k_1k.code, self.coupon_all_10pct.code],
        )

        self.assertEqual(price_res.discounted, Decimal("18900.00"))
        self.assertEqual(
            applied_coupons,
            ["최소 5,000원 1,000원 할인", "전체 10% 할인"]
        )
        self.assertListEqual(price_res.discount_types, ["FIXED", "PERCENTAGE"])


    # 15) 프로모션 없고, coupon_code 파라미터로 빈 리스트([]) 전달 → 원가
    def test_프로모션없고_빈쿠폰리스트(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book1)

        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("5000.00"),
                discounted=Decimal("5000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book1,
            user=None,
            coupon_code=[],
        )

        # 빈 리스트를 넘겨도 coupon_code가 False 처리되어, 원가 그대로 리턴
        self.assertEqual(price_res.discounted, Decimal("5000.00"))
        self.assertEqual(applied_coupons, [])


    # 16) 프로모션 존재, coupon_code=None 전달 → 프로모션만 적용
    def test_프로모션만_빈쿠폰리스트(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        # PromotionService: 프로모션 5%만 적용
        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.side_effect = lambda product_code, original_price, user=None: (
            PriceResultEntity(
                original=original_price,
                discounted=(original_price * Decimal("0.95")).quantize(Decimal("0.01")),
                discount_amount=(original_price - original_price * Decimal("0.95")).quantize(Decimal("0.01")),
                discount_types=["PERCENTAGE"]
            ),
            True,
            "ALL_5PERCENT_PROMO"
        )

        # CouponService: 후보가 실제로 없도록 빈 리스트 리턴
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=None,
        )

        # 프로모션 5%만 한 번 적용 → 22,000 * 0.95 = 20,900
        self.assertEqual(len(available_coupons), 0)
        self.assertEqual(applied_coupons, ["ALL_5PERCENT_PROMO"])
        self.assertEqual(price_res.discounted, Decimal("20900.00"))
        self.assertEqual(price_res.discount_amount, Decimal("1100.00"))
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])


    # 17) 프로모션 이후, “전체 대상 10%” 쿠폰과 “상품 전용 5,000원” 쿠폰을 동시에 적용
    def test_프로모션후_복수쿠폰순서(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        # 프로모션: 전체 대상 5% 적용
        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.side_effect = lambda product_code, original_price, user=None: (
            PriceResultEntity(
                original=original_price,
                discounted=(original_price * Decimal("0.95")).quantize(Decimal("0.01")),
                discount_amount=(original_price - original_price * Decimal("0.95")).quantize(Decimal("0.01")),
                discount_types=["PERCENTAGE"]
            ),
            True,
            "ALL_5PERCENT_PROMO"
        )

        # 두 후보 쿠폰: ALL10, B2FIX5K
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_all_10pct, self.coupon_book2_5k],
            get_coupons_by_code=lambda codes: [
                c for c in [self.coupon_all_10pct, self.coupon_book2_5k] if c.code in codes
            ],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # (22,000 * 0.95 = 20,900) → (20,900 * 0.9 = 18,810) → (18,810 - 5,000 = 13,810)
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_all_10pct.code, self.coupon_book2_5k.code],
        )

        self.assertEqual(price_res.discounted, Decimal("13810.00"))
        self.assertIn("ALL_5PERCENT_PROMO", applied_coupons)
        self.assertIn("전체 10% 할인", applied_coupons)
        self.assertIn("도서2 전용 5,000원 할인", applied_coupons)
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE", "FIXED"])


    # 18) “전체 대상 10%” 쿠폰과 “상품 전용 5,000원” 쿠폰을 순서 반대로 적용
    def test_복수쿠폰순서_반대로(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        # 프로모션 없음
        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        # 두 후보 쿠폰: MIN5K1K, ALL10
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_min5k_1k, self.coupon_all_10pct],
            get_coupons_by_code=lambda codes: [
                c for c in [self.coupon_min5k_1k, self.coupon_all_10pct] if c.code in codes
            ],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # (22,000 - 1,000 = 21,000) → (21,000 *0.9 = 18,900)
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_min5k_1k.code, self.coupon_all_10pct.code],
        )

        self.assertEqual(price_res.discounted, Decimal("18900.00"))
        self.assertEqual(
            applied_coupons,
            ["최소 5,000원 1,000원 할인", "전체 10% 할인"]
        )
        self.assertListEqual(price_res.discount_types, ["FIXED", "PERCENTAGE"])


    # 19) get_coupons_by_code에서 일부 코드만 리턴 → 나머지는 무시
    def test_부분리턴된쿠폰_무시(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        # 프로모션 없음
        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.return_value = (
            PriceResultEntity(
                original=Decimal("22000.00"),
                discounted=Decimal("22000.00"),
                discount_amount=Decimal("0.00"),
                discount_types=[]
            ),
            False,
            ""
        )

        # get_applicable_coupons에선 두 가지 쿠폰 후보 (ALL10 + B2FIX5K)을 올려두지만,
        # get_coupons_by_code에서는 “ALL10만” 리턴 → B2FIX5K는 무시되어야 함
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [self.coupon_all_10pct, self.coupon_book2_5k],
            get_coupons_by_code=lambda codes: [self.coupon_all_10pct],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # 두 개 쿠폰 코드를 전달했지만 get_coupons_by_code에서는 ALL10만 리턴 → B2FIX5K 무시
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=[self.coupon_all_10pct.code, self.coupon_book2_5k.code],
        )

        # 10%만 적용 → 22,000 * 0.9 = 19,800
        self.assertEqual(price_res.discounted, Decimal("19800.00"))
        self.assertEqual(applied_coupons, ["전체 10% 할인"])
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])


    # 20) 프로모션은 한 개, 쿠폰 후보엔 하나도 없으나 coupon_code에는 잘못된 코드 전달 → 프로모션만 적용
    def test_프로모션만_잘못된쿠폰코드(self):
        mock_repo = mock.Mock(get_product_by_code=lambda code: self.book2)

        # 프로모션: BOOK2에 10% 적용
        mock_promo_service = mock.Mock()
        mock_promo_service.apply_policy.side_effect = lambda product_code, original_price, user=None: (
            PriceResultEntity(
                original=original_price,
                discounted=(original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_amount=(original_price - original_price * Decimal("0.90")).quantize(Decimal("0.01")),
                discount_types=["PERCENTAGE"]
            ),
            True,
            "BOOK2_10PERCENT_PROMO"
        )

        # get_applicable_coupons → 빈 리스트, get_coupons_by_code → 빈 리스트 (올바르지 않은 coupon_code 전달)
        mock_coupon_service = mock.Mock(
            get_applicable_coupons=lambda **kwargs: [],
            get_coupons_by_code=lambda codes: [],
        )

        use_case = CalculatePriceUseCase(
            product_repo=mock_repo,
            promotion_service=mock_promo_service,
            coupon_service=mock_coupon_service,
        )

        # coupon_code에 잘못된 코드 전달
        available_coupons, applied_coupons, price_res = use_case.execute(
            product=self.book2,
            user=None,
            coupon_code=["INVALID_CODE"],
        )

        # 쿠폰은 전혀 적용되지 않으므로, 프로모션만 적용된 상태
        self.assertEqual(price_res.discounted, Decimal("19800.00"))
        self.assertEqual(applied_coupons, ["BOOK2_10PERCENT_PROMO"])
        self.assertListEqual(price_res.discount_types, ["PERCENTAGE"])
