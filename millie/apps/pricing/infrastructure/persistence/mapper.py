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

    # def to_domain(self, coupon: CouponModel) -> CouponDomainEntity:
    #     # DiscountPolicy에 연결된 DiscountTarget들 가져오기
    #     discount_targets = coupon.discount_policy.discounttarget_set.all().order_by('apply_priority')
    #     target_user_ids = [dt.target_user_id_id for dt in discount_targets if dt.target_user_id_id is not None]
    #     target_product_codes = [dt.target_product_code_id for dt in discount_targets if dt.target_product_code_id is not None]
    #     discount_policy = self.discount_policy_mapper.to_domain(coupon.discount_policy)

    #     return CouponDomainEntity(
    #         id=coupon.id,
    #         code=coupon.code,
    #         name=coupon.name,
    #         # discount_policy=coupon.discount_policy,
    #         discount_policy=discount_policy,
    #         valid_until=coupon.valid_until,
    #         status=coupon.status,
    #         is_active=coupon.status == CouponStatus.ACTIVE.value,
    #         minimum_purchase_amount=coupon.discount_policy.minimum_purchase_amount,
    #         target_product_code=target_product_codes,  # 리스트로 반환
    #         target_user_id=target_user_ids,            # 리스트로 반환
    #         created_at=coupon.created_at,
    #         updated_at=coupon.updated_at,
    #     )


    def to_domain(self, coupon_model: CouponModel) -> CouponDomainEntity:
        """
        CouponModel → 도메인 CouponEntity 로 변환
        """
        # 1) CouponModel.discount_policy (ForeignKey) 에 연결된 DiscountPolicyModel 을 꺼내기
        policy_model = coupon_model.discount_policy
        if policy_model is None:
            # 실제 DB에는 Null 이면 안 되므로, 이 시점에 None 이면 무조건 오류
            raise RuntimeError(f"Coupon(id={coupon_model.id})에 연결된 DiscountPolicy가 없습니다.")

        # 2) DiscountPolicyModel → 도메인 전략 객체
        if isinstance(policy_model, DiscountPolicyModel):
            print("=" * 100)
            print(policy_model.discount_type)
            print("=" * 100)
            strategy = self.discount_policy_mapper.to_domain(policy_model)
        else:
            strategy = policy_model

        # 3) DiscountTarget(할인 대상) 정보 중, 우선순위 가장 높은 레코드를 꺼내서
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

        # 4) CouponDomainEntity 생성 시, "할인 정책 전략 객체"를 포함한 모든 필드를 넘겨 준다.
        return CouponDomainEntity(
            id                      = coupon_model.id,
            code                    = coupon_model.code,
            name                    = coupon_model.name,
            discount_policy         = strategy,
            # discount_policy         = policy_model,
            valid_until             = coupon_model.valid_until,
            status                  = coupon_model.status,
            created_at              = coupon_model.created_at,
            updated_at              = coupon_model.updated_at,
            # 아래 필드들은 dataclass 에 정의되어 있어야 함
            target_type             = policy_model.target_type,
            target_product_code     = target_product_code,
            target_user_id          = target_user_id,
            is_active               = policy_model.is_active,
            minimum_purchase_amount = policy_model.minimum_purchase_amount,
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
