from django.utils import timezone
from typing import Optional
from uuid import UUID

from apps.pricing.domain.discount_policy import PriceResult
from apps.pricing.domain.repository import CouponRepository
from apps.product.domain.repository import ProductRepository

class PricingService:
    def __init__(
        self,
        coupon_repo: CouponRepository,
        product_repo: ProductRepository,
    ):
        self.coupon_repo = coupon_repo
        self.product_repo = product_repo

    def calculate_final_price(
        self,
        product_code: str,
        coupon_code: Optional[str] = None,
    ) -> PriceResult:
        product = self.product_repo.get_product_by_code(product_code)
        base_price = product.price

        # 할인 정책 조회
        policy = self.coupon_repo.get_discount_policy_by_code(product_code)

        if policy:
            price_result = policy.apply(base_price)

        # 쿠폰이 있다면 추가로 적용
        if coupon_code:
            coupon = self.coupon_repo.get_coupon_by_code(coupon_code)
            if coupon and self._validate_coupon(coupon_code, product_code):
                price_result = coupon.discount_policy.apply(price_result.discounted)

        if not (policy or coupon_code):
            price_result = PriceResult(
                original=base_price,
                discounted=base_price - (base_price * product.discount_rate),
                discount_amount=base_price * product.discount_rate,
                discount_type="default",
            )

        return price_result


    def _validate_coupon(
        self,
        coupon_code: UUID,
        product_code: str,
    ) -> bool:
        coupon = self.coupon_repo.get_coupon_by_code(coupon_code)
        product = self.product_repo.get_product_by_code(product_code)

        # 기간
        if coupon and coupon.valid_until < timezone.now():
            return False

        # 최소 적용금액이 설정된 쿠폰인 경우
        if coupon and coupon.minimum_purchase_amount > 0:
            if product.price < coupon.minimum_purchase_amount:
                return False

        # 특정 상품에만 사용가능한경우
        if coupon and coupon.target_product_code and coupon.target_product_code != product_code:
            return False

        # 특정 유저만 사용가능한 경우
        # if coupon and coupon.target_user_id and coupon.target_user_id != user_id:
        #     return False
