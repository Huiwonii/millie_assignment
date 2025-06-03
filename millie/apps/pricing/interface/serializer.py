from rest_framework import serializers


class CouponSummarySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    discount_type = serializers.CharField()
    discount_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    target_type = serializers.CharField()
    target_product_code = serializers.CharField()
    target_user_id = serializers.UUIDField()
    minimum_purchase_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    valid_until = serializers.DateTimeField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()

class PriceResultSerializer(serializers.Serializer):
    original = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_types = serializers.ListField(child=serializers.CharField(), allow_empty=True)