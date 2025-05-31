from apps.pricing.domain.entity import Coupon as CouponDomainEntity
from apps.pricing.domain.discount_policy import DiscountPolicy as DiscountPolicyDomainEntity
from apps.pricing.domain.discount_policy import PercentageDiscountPolicy, FixedDiscountPolicy
from apps.pricing.domain.value_objects import DiscountType
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.infrastructure.persistence.models import DiscountPolicy as DiscountPolicyModel


class CouponMapper:

    def __init__(self):
        self.discount_policy_mapper = DiscountPolicyMapper()

    def to_domain(self, coupon: CouponModel) -> CouponDomainEntity:
        return CouponDomainEntity(
            id=coupon.id,
            code=coupon.code,
            name=coupon.name,
            discount_policy=self.discount_policy_mapper.to_domain(coupon.discount_policy),
            valid_until=coupon.valid_until,
            status=coupon.status,
            created_at=coupon.created_at,
            updated_at=coupon.updated_at,
        )


class DiscountPolicyMapper:
    def to_domain(self, model: DiscountPolicyModel) -> DiscountPolicyDomainEntity:
        if model.discount_type == DiscountType.PERCENTAGE:
            return PercentageDiscountPolicy(
                discount_type=model.discount_type,
                discount_rate=model.value,
            )
        elif model.discount_type == DiscountType.FIXED:
            return FixedDiscountPolicy(
                discount_type=model.discount_type,
                discount_amount=model.value,
            )