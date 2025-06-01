from rest_framework import serializers



class CouponSummarySerializer(serializers.Serializer):
    """
    클라이언트에게 “상품 상세 페이지에 보여줄 쿠폰 요약 정보”만 내려주기 위한 직렬화기
    """
    code = serializers.CharField()   # 쿠폰 코드
    name = serializers.CharField()   # 쿠폰 이름
    # discount_type/value는 실제 적용 가능한 쿠폰이다 보니, “할인 유형”과 “할인 값” 정도를 노출
    discount_type = serializers.CharField()
    discount_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # min_purchase_amount = serializers.DecimalField(
    #     source="discount_policy.minimum_purchase_amount",
    #     max_digits=10,
    #     decimal_places=2
    # )
    # valid_until = serializers.DateTimeField()
    # status = serializers.CharField()
    # (원한다면) min_purchase_amount, valid_until 등도 같이 리턴해 줄 수 있습니다.

    # 만약 CouponDomainEntity가 @dataclass로 정의되어 있고,
    # 내부에 discount_policy: DiscountPolicy 도메인 객체를 갖고 있다면,
    # Serializer가 source="discount_policy.discount_type" 등을 읽을 수 있습니다.




class PriceResultSerializer(serializers.Serializer):
    original = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.CharField()