from rest_framework import serializers



class CouponSummarySerializer(serializers.Serializer):

    code = serializers.CharField()
    name = serializers.CharField()
    discount_type = serializers.CharField()
    discount_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )


class PriceResultSerializer(serializers.Serializer):
    original = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_types = serializers.ListField(child=serializers.CharField(), allow_empty=True)