# apps/pricing/application/use_case.py

from typing import List, Optional
from decimal import Decimal
from django.utils import timezone

from apps.pricing.infrastructure.persistence.repository_impl import DiscountPolicyRepoImpl
from apps.pricing.domain.entity.price_result import PriceResult
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyStrategy
from apps.pricing.domain.policy.discount_policy import (
    PercentageDiscountPolicy,
    FixedDiscountPolicy,
)
from apps.pricing.domain.value_objects import DiscountType
from apps.pricing.infrastructure.persistence.mapper import CouponMapper


class DiscountService:
    def __init__(self):
        self.dp_repo = DiscountPolicyRepoImpl()
        self.coupon_repo = DiscountPolicyRepoImpl()
        # DiscountPolicyRepositoryImpl은 DiscountPolicyModel/DiscountTargetModel 기준으로
        # “적용 우선순위가 가장 높은 DiscountPolicyModel 하나”를 꺼내서
        # DiscountPolicyMapper.to_domain(...)을 통해 Strategy 객체를 리턴하는 메서드를 가집니다.

    def apply_best_policy(
        self,
        product_code: str,
        original_price: Decimal,
        user = None,
    ) -> PriceResult:
        """
        1) DiscountTargetModel.filter(target_product_code=product_code, target_user_id=user.id) ... 
           우선순위(apply_priority) 기준으로 .order_by('apply_priority').first() 로 하나 선택
        2) 선택된 policy_model 을 DiscountPolicyMapper.to_domain(...) → Percentage/Fixed 전략 객체
        3) strategy.apply(original_price) → PriceResult 리턴
        """
        strategy_list: Optional[List[DiscountPolicyStrategy]] = self.dp_repo.get_discount_policies(
            target_product_code=product_code,
            target_user_id=user.id if user else None,
        )
        if not strategy_list:
            # 적용할 정책이 없으면 그대로 PriceResult를 리턴 (할인 없음)
            return PriceResult(
                original=original_price,
                discounted=original_price,
                discount_amount=Decimal("0"),
            )
        # apply() 시 “추가 할인 전 이미 할인된 금액”은 0
        best_strategy = strategy_list[0]
        return best_strategy.apply(original_price)




class CouponService:
    def __init__(self):
        # self.coupon_repo = CouponRepositoryImpl()
        self.dp_repo = DiscountPolicyRepoImpl()
        self.coupon_repo = DiscountPolicyRepoImpl()
        self.coupon_mapper = CouponMapper()

    def get_applicable_coupons(
        self,
        product_code: str,
        user,
    ) -> List[CouponDomainEntity]:
        """
        1) CouponModel.objects.filter(status='active', valid_until__gte=now)
        2) 각각의 CouponModel → CouponMapper.to_domain(...)
        3) domain_coupon.is_active 검사
        4) 상품적용/사용자적용 대상이거나 전체 대상인 것만 필터링해서 List 리턴
        """
        now = timezone.now()
        coupons = self.coupon_repo.list_active_not_expired(now)

        result: List[CouponDomainEntity] = []
        for coupon in coupons:
            # if coupon.is_active and coupon.is_available(user, product_code):
            if coupon.is_available(user, product_code):
                result.append(coupon)

        return result

    def get_coupon_by_code(
        self,
        coupon_code: str,
    ) -> Optional[CouponDomainEntity]:
        """
        1) CouponModel.objects.get(code=coupon_code)
        2) CouponMapper.to_domain(...)
        3) (valid_until, status 검사 등) 
        """
        coupon = self.coupon_repo.get_coupon_by_code(coupon_code)
        if not coupon:
            return None
        return coupon
