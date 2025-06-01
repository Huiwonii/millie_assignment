# apps/product/application/product_detail_use_case.py

from typing import Optional, Tuple, List
from decimal import Decimal
from datetime import datetime

from apps.product.domain.entity import Product as ProductEntity
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.pricing.application.discount_service import DiscountService
from apps.pricing.application.discount_service import CouponService
from apps.pricing.domain.entity.price_result import PriceResult
from apps.product.domain.value_objects import ProductStatus
from apps.pricing.domain.policy.discount_policy import DiscountPolicy as DiscountPolicyStrategy
from apps.pricing.domain.entity.price_result import PriceResult as PriceResultEntity
from apps.pricing.domain.entity.coupon import Coupon as CouponDomainEntity



class ProductDetailUseCaseBak:
    def __init__(
        self,
        product_repo: ProductRepositoryImpl,
        discount_service: DiscountService,
        coupon_service: CouponService,
    ):
        self.product_repo = product_repo
        self.discount_service = discount_service
        self.coupon_service = coupon_service

    def execute(
        self,
        code: str,
        user = None,                    # 현재 로그인한 User 객체(또는 None)
        coupon_code: Optional[str] = None,
    ) -> Tuple[ProductEntity, List, PriceResult]:
        """
        반환값:
          - ProductEntity: DB에서 찾은 책 도메인 엔티티
          - List[CouponDomainEntity]: 해당 상품·사용자에게 적용 가능한 쿠폰 리스트
          - PriceResult: (원가, 할인 후 가격, 할인 금액) ⋯ 사용자가 coupon_code를 넘겼다면 쿠폰까지 적용된 결과
        """

        # 1)  상품 정보 조회
        product_entity: ProductEntity = self.product_repo.get_product_by_code(code)
        if not product_entity or product_entity.status != ProductStatus.ACTIVE.value:
            # 존재하지 않거나 판매 불가 상태라면 예외 처리
            raise Exception(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")

        # 2)  “해당 상품+해당 사용자”에게 유효한 쿠폰 목록 가져오기
        #     (CouponService 내부에서 DiscountPolicy / DiscountTarget 기준 + valid_until 검사 등)
        applicable_coupons = self.coupon_service.get_applicable_coupons(
            product_code=code,
            user=user,
        )
        print("B" * 100)
        print(applicable_coupons)
        print("B" * 100)
        #    → List[CouponDomainEntity]

        # 3)  “기본 할인(상품별/전체) 적용” 후 중간 가격 계산
        #     DiscountService 내부에서 DiscountTarget 테이블을 참조하여
        #     “상품이 속한(또는 전체 대상) 할인 정책”을 우선순위별 처리 → PriceResult 리턴
        base_price = product_entity.price
        base_price_result: PriceResult = self.discount_service.apply_best_policy(
            product_code=code,
            user=user,
            original_price=base_price,
        )
        #    → PriceResult(original=base_price, discounted=after_discounted, discount_amount=discount_amt)

        # 4)  만약 “coupon_code”가 쿼리 파라미터로 넘어왔다면,
        #     “그 쿠폰이 실제로 적용 가능한지(is_available) 검사 → 해당 쿠폰을 DiscountPolicy 형태로 바꿔서 추가 적용 → PriceResult 계산”
        final_price_result = base_price_result
        if coupon_code:
            # CouponService에서 “코드를 주면 쿠폰 도메인 + 도메인 할인 정책”을 dto로 리턴하도록 한다
            coupon_domain = self.coupon_service.get_coupon_by_code(coupon_code)
            if coupon_domain is not None:
                # “쿠폰이 상품·유저에 유효한지 내부 is_available() 검사 통과한 경우에만”
                if coupon_domain.is_available(user, product_entity):
                    coupon_policy = coupon_domain.to_discount_policy()  # → DiscountPolicy 전략 객체
                    # 이미 base_price_result.discounted 만큼으로 가격이 내려갔으므로, 그 가격을 넘겨서 “쿠폰 할인” 재적용
                    final_price_result = coupon_policy.apply(
                        price=base_price_result.discounted,
                        already_discounted_amount=base_price_result.discount_amount,
                    )
                # else: 쿠폰은 있지만 상품/유저 대상이 아니므로 무시 → base_price_result 그대로 둔다
            # else: coupon_domain이 None → 코드가 틀렸거나 없는 쿠폰 → base_price_result 그대로

        # 5)  최종 리턴
        return product_entity, applicable_coupons, final_price_result




# apps/product/application/product_detail_use_case.py


class ProductDetailUseCase:
    def __init__(
        self,
        product_repo: ProductRepositoryImpl,
        discount_service: DiscountService,
        coupon_service: CouponService,
    ):
        self.product_repo = product_repo
        self.discount_service = discount_service
        self.coupon_service = coupon_service


    def execute(
        self,
        code: str,
        user=None,
        coupon_code: Optional[str] = None,
    ) -> Tuple[ProductEntity, List[CouponDomainEntity], PriceResult]:
        # 1) 상품 조회
        product_entity: ProductEntity = self.product_repo.get_product_by_code(code)
        if not product_entity or product_entity.status != ProductStatus.ACTIVE.value:
            # 존재하지 않거나 판매 불가 상태라면 예외 처리
            raise Exception(f"해당 코드({code})의 상품이 없거나 판매 불가 상태입니다.")


        # 2) 적용 가능한 쿠폰 목록 조회
        applicable_coupons = self.coupon_service.get_applicable_coupons(
            product_code=code,
            user=user,
        )

        # 3) 기본 할인 적용
        base_price = product_entity.price
        base_price_result: PriceResultEntity = self.discount_service.apply_best_policy(
            product_code=code,
            user=user,
            original_price=base_price,
        )

        # 4) 쿠폰 코드가 넘어왔다면 쿠폰 추가 할인 적용
        final_price_result = base_price_result
        if coupon_code:
            coupon_domain = self.coupon_service.get_coupon_by_code(coupon_code)
            # 4-1) coupon_domain 자체가 None이면 “잘못된 쿠폰 코드 or 이미 만료”이니 무시
            if coupon_domain is not None:
                # 4-2) 쿠폰이 실제 “상품/사용자 대상 + 유효 기간 + is_active”를 모두 통과해야 적용
                if coupon_domain.is_available(user, product_entity.code):
                    # 4-3) 이제 쿠폰 도메인 안에는 discount_policy(전략 객체)가 반드시 채워져 있어야 한다
                    strategy: DiscountPolicyStrategy = coupon_domain.to_discount_policy()
                    # base_price_result.discounted가 이미 적용된 가격이므로
                    # “현재 금액”과 “지금까지 할인된 금액(base_price_result.discount_amount)”를 넘겨준다
                    # final_price_result = strategy.apply(
                    #     price=base_price_result.discounted,
                    #     already_discounted_amount=base_price_result.discount_amount,
                    # )
                    final_price_result = strategy.apply(base_price_result.discounted)
                else:
                    # 쿠폰은 존재하지만 “이 상품/사용자에는 못 쓰는 쿠폰”이므로 그냥 무시
                    final_price_result = base_price_result
            else:
                # coupon_domain is None인 경우(코드가 틀렸거나 이미 만료되었거나)
                final_price_result = base_price_result

        # 5) 리턴
        return product_entity, applicable_coupons, final_price_result
