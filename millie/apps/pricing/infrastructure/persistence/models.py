from uuid import UUID
from django.db import models
from apps.product.infrastructure.persistence.models import Book
from apps.pricing.domain.value_objects import (
    TargetType,
    DiscountType,
    CouponStatus,
)


class DiscountPolicy(models.Model):

    id = models.UUIDField(primary_key=True, default=UUID, editable=False)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices(), null=False, db_comment="할인 유형")
    value = models.DecimalField(max_digits=10, decimal_places=2, null=False, db_comment="할인율 또는 정액 값")
    target_type = models.CharField(
        max_length=20,
        choices=TargetType.choices(),
        default=TargetType.ALL,
        null=False,
        db_comment="할인 정책 타입"
    )
    is_active = models.BooleanField(default=True, db_comment="활성 상태")
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_comment="최소 구매 금액")
    effective_start_at = models.DateTimeField(null=False, db_comment="시작 일자")
    effective_end_at = models.DateTimeField(null=False, db_comment="종료 일자")
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discount_policies"
        db_table_comment = "할인 정책 테이블"


class DiscountTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID, editable=False)
    discount_policy = models.ForeignKey(DiscountPolicy, null=False, on_delete=models.CASCADE, db_comment="할인 정책")
    target_user = models.ForeignKey("User", to_field="id", null=True, on_delete=models.CASCADE, db_comment="사용자에 적용되는 경우 값 있음")
    target_product_code = models.ForeignKey(Book, to_field="code", null=True, on_delete=models.CASCADE, db_comment="상품에 적용되는 경우 값 있음")
    apply_priority = models.IntegerField(null=False, db_comment="적용 우선순위")
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discount_targets"
        db_table_comment = "할인 정책 타겟 테이블"


class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID, editable=False)
    code = models.CharField(max_length=255, null=False, db_comment="쿠폰 코드")
    name = models.CharField(max_length=255, null=False, db_comment="쿠폰 이름")
    # way_to_issue = models.CharField(max_length=255, null=False, db_comment="발급 방식") # TODO! 삭제검토
    valid_until = models.DateTimeField(null=False, db_comment="유효 기간")
    status = models.CharField(max_length=255, null=False, db_comment="사용 상태")
    discount_policy = models.ForeignKey(DiscountPolicy, null=False, on_delete=models.CASCADE, db_comment="할인 정책")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "coupons"
        db_table_comment = "쿠폰 테이블"


class User(models.Model):
    """
    사용자 도메인은 본 과제의 핵심 구현이 아니지만 할인정책의 확장성을 설계하기 위해 추가
    (원래 모델도 이 도메인 안에 포함되어서는 안됨)
    """
    id = models.UUIDField(primary_key=True, default=UUID, editable=False)
    name = models.CharField(max_length=255, null=False, db_comment="사용자 이름")
    ...

    class Meta:
        db_table = "users"
        db_table_comment = "사용자 테이블"



# class IssuedCoupon(models.Model):
#     """
#     Coupon을 발급하는 경우 발급된 쿠폰의 정보를 저장하는 테이블
#     (각 유저에 대한 개별발급 확장 가능성)
#     """
#     id = models.UUIDField(primary_key=True, default=UUID, editable=False)
#     coupon = models.ForeignKey(Coupon, to_field="code", null=False, on_delete=models.CASCADE, db_comment="쿠폰")
#     issued_coupon_id = models.CharField(max_length=255, null=False, db_comment="발급된 쿠폰 id")  # 난수번호등
#     user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, db_comment="사용자")    # 특정 사용자만 사용가능하도록 하는 쿠폰의 경우
#     ...
#     created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
#     updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

