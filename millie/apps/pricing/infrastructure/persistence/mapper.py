from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyDomainEntity
from apps.pricing.domain.policy.discount_policy import (
    PercentageDiscountPolicy,
    FixedDiscountPolicy,
)
from apps.pricing.domain.value_objects import (
    DiscountType,
    CouponStatus,
)
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.infrastructure.persistence.models import DiscountPolicy as DiscountPolicyModel
from apps.pricing.infrastructure.persistence.models import DiscountTarget as DiscountTargetModel
from apps.pricing.domain.entity.price_result import PriceResult

class CouponMapper:

    def __init__(self):
        self.discount_policy_mapper = DiscountPolicyMapper()


    def to_domain(self, coupon_model: CouponModel) -> CouponDomainEntity:
        policy_model = coupon_model.discount_policy

        # DiscountPolicyModel → 도메인 전략 객체
        strategy = self.discount_policy_mapper.to_domain(policy_model)

        # DiscountTarget(할인 대상) 정보 중, 우선순위 가장 높은 레코드
        dt_model = (
            DiscountTargetModel.objects
            .filter(discount_policy=policy_model)
            .order_by("apply_priority")
            .first()
        )
        target_product_code = None
        target_user_id = None

        if dt_model:
            if dt_model.target_product_code:
                target_product_code = dt_model.target_product_code.code
            if dt_model.target_user_id:
                target_user_id = dt_model.target_user_id.id

        return CouponDomainEntity(id=coupon_model.id,
            code=coupon_model.code,
            name=coupon_model.name,
            discount_policy=strategy,  # 도메인 전략 객체
            valid_until=coupon_model.valid_until,
            status=coupon_model.status,
            created_at=coupon_model.created_at,
            updated_at=coupon_model.updated_at,
            target_type=policy_model.target_type,
            target_product_code=target_product_code,
            target_user_id=target_user_id,
            is_active=policy_model.is_active,
            minimum_purchase_amount=policy_model.minimum_purchase_amount,
        )


class DiscountPolicyMapper:
    def to_domain(
        self,
        model: DiscountPolicyModel,
    ) -> DiscountPolicyDomainEntity:
        if model.discount_type == DiscountType.PERCENTAGE.value:
            return PercentageDiscountPolicy(
                discount_type=model.discount_type,
                discount_rate=model.value,
            )
        elif model.discount_type == DiscountType.FIXED.value:
            return FixedDiscountPolicy(
                discount_type=model.discount_type,
                discount_amount=model.value,
            )
