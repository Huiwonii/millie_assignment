from rest_framework import serializers



class CouponSummarySerializer(serializers.Serializer):

    code = serializers.CharField()
    name = serializers.CharField()
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




class PriceResultSerializer(serializers.Serializer):
    original = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.CharField()