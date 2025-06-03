from apps.pricing.domain.entity.coupon import Coupon as CouponEntity
from apps.pricing.domain.policy.discount_policy import (
    DiscountPolicy,
    FixedDiscountPolicy,
    PercentageDiscountPolicy,
)
from apps.pricing.domain.entity.promotion import Promotion as PromotionEntity
from apps.pricing.domain.value_objects import DiscountType
from apps.pricing.infrastructure.persistence.models import Coupon as CouponModel
from apps.pricing.infrastructure.persistence.models import DiscountPolicy as DiscountPolicyModel
from apps.pricing.infrastructure.persistence.models import DiscountTarget as DiscountTargetModel
from apps.pricing.infrastructure.persistence.models import Promotion as PromotionModel


class CouponMapper:

    def __init__(self):
        self.discount_policy_mapper = DiscountPolicyMapper()

    def to_domain(self, coupon_model: CouponModel) -> CouponEntity:
        policy_model = coupon_model.discount_policy
        strategy = self.discount_policy_mapper.to_domain(policy_model)

        discount_target_model = (
            DiscountTargetModel.objects
            .filter(discount_policy=policy_model)
            .order_by("apply_priority", "created_at")
            .first()
        )
        target_product_code = None
        target_user_id = None

        if discount_target_model:
            if discount_target_model.target_product_code:
                target_product_code = discount_target_model.target_product_code.code
            if discount_target_model.target_user_id:
                target_user_id = discount_target_model.target_user_id.id

        return CouponEntity(id=coupon_model.id,
            code=coupon_model.code,
            name=coupon_model.name,
            discount_policy=strategy,
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
    ) -> DiscountPolicy:
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


class PromotionMapper:

    def __init__(self):
        self.discount_policy_mapper = DiscountPolicyMapper()

    def to_domain(self, promotion_model: PromotionModel) -> PromotionEntity:

        return PromotionEntity(
            id=promotion_model.id,
            name=promotion_model.name,
            discount_policy=self.discount_policy_mapper.to_domain(promotion_model.discount_policy),
            is_auto_discount=promotion_model.is_auto_discount,
            apply_priority=promotion_model.discount_policy.apply_priority,
            created_at=promotion_model.created_at,
            updated_at=promotion_model.updated_at,
        )