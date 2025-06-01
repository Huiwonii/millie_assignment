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


class CouponMapper:

    def __init__(self):
        self.discount_policy_mapper = DiscountPolicyMapper()

    def to_domain(self, coupon: CouponModel) -> CouponDomainEntity:
        # DiscountPolicy에 연결된 DiscountTarget들 가져오기
        discount_targets = coupon.discount_policy.discounttarget_set.all().order_by('apply_priority')
        target_user_ids = [dt.target_user_id_id for dt in discount_targets if dt.target_user_id_id is not None]
        target_product_codes = [dt.target_product_code_id for dt in discount_targets if dt.target_product_code_id is not None]

        return CouponDomainEntity(
            id=coupon.id,
            code=coupon.code,
            name=coupon.name,
            discount_policy=coupon.discount_policy,
            valid_until=coupon.valid_until,
            status=coupon.status,
            is_active=coupon.status == CouponStatus.ACTIVE.value,
            minimum_purchase_amount=coupon.discount_policy.minimum_purchase_amount,
            target_product_code=target_product_codes,  # 리스트로 반환
            target_user_id=target_user_ids,            # 리스트로 반환
            created_at=coupon.created_at,
            updated_at=coupon.updated_at,
        )


class DiscountPolicyMapper:
    def to_domain(self, model: DiscountPolicyModel) -> DiscountPolicyDomainEntity:
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
        # else:
        #     raise ValueError(f"Invalid discount type: {model.discount_type}")