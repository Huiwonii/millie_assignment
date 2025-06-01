import pytest
from decimal import Decimal

from apps.product.application.product_detail_use_case import ProductDetailUseCase
from apps.product.domain.entity import Product as ProductEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity
from apps.pricing.domain.policy.discount_policy import PercentageDiscountPolicy
from apps.pricing.domain.entity.price_result import PriceResult

@pytest.fixture
def product_entity():
    return ProductEntity(
        code="BOOK002",
        name="테스트 도서 2",
        price=Decimal("22000.00"),
        status="ACTIVE",
        created_at="",
        updated_at=""
    )

@pytest.fixture
def coupon_10_percent():
    return CouponDomainEntity(
        id="0bae76ec-7230-41c1-9297-3461bd8aa115",
        code="COUPON03",
        name="테스트 쿠폰 3",
        discount_policy=PercentageDiscountPolicy("PERCENTAGE", Decimal("0.10")),
        valid_until="2025-12-31T23:59:59Z",
        status="ACTIVE",
        created_at="2024-01-31T23:59:59Z",
        updated_at="",
        target_type="ALL",
        target_product_code=None,
        target_user_id=None,
        minimum_purchase_amount=Decimal("15000.00"),
        is_active=True,
    )

@pytest.fixture
def coupon_5000_fixed():
    return CouponDomainEntity(
        id="0bae76ec-7230-41c1-9297-3461bd8aa115",
        code="COUPON03",
        discount_policy=PercentageDiscountPolicy("FIXED", Decimal("5000")),
        valid_until="2025-12-31T23:59:59Z",
        status="ACTIVE",
        created_at="",
        updated_at="",
        target_type="PRODUCT",
        minimum_purchase_amount=Decimal("0")
    )

def test_쿠폰없으면_정가반환(product_entity, mocker):
    # given
    use_case = ProductDetailUseCase(
        product_repo=mocker.Mock(get_product_by_code=lambda code: product_entity),
        discount_service=mocker.Mock(),
        coupon_service=mocker.Mock(get_applicable_coupons=lambda **kwargs: [], get_coupons_by_code=lambda code: []),
    )
    # when
    product, coupons, price_result = use_case.execute(code="BOOK002", user=None, coupon_code=None)
    # then
    assert price_result.original == Decimal("22000.00")
    assert price_result.discounted == Decimal("22000.00")
    assert price_result.discount_amount == 0

def test_쿠폰한개적용시_할인(product_entity, coupon_10_percent, mocker):
    # given
    use_case = ProductDetailUseCase(
        product_repo=mocker.Mock(get_product_by_code=lambda code: product_entity),
        discount_service=mocker.Mock(),
        coupon_service=mocker.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_10_percent],
            get_coupons_by_code=lambda code: [coupon_10_percent],
        ),
    )
    # when
    product, coupons, price_result = use_case.execute(code="BOOK002", user=None, coupon_code=["COUPON03"])
    # then
    assert price_result.discounted == Decimal("19800.00")  # 22000 * 0.9

def test_쿠폰여러개_누적적용시_할인(product_entity, coupon_10_percent, coupon_5000_fixed, mocker):
    # given
    use_case = ProductDetailUseCase(
        product_repo=mocker.Mock(get_product_by_code=lambda code: product_entity),
        discount_service=mocker.Mock(),
        coupon_service=mocker.Mock(
            get_applicable_coupons=lambda **kwargs: [coupon_10_percent, coupon_5000_fixed],
            get_coupons_by_code=lambda code: [coupon_10_percent, coupon_5000_fixed],
        ),
    )
    # when
    product, coupons, price_result = use_case.execute(code="BOOK002", user=None, coupon_code=["COUPON03", "COUPON02"])
    # then
    # 22000 -> 19800 (10% 할인) -> 14800 (5000원 할인)
    assert price_result.discounted == Decimal("14800.00")
