from rest_framework import serializers
from apps.product.domain.entity import Product


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    author = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()
    published_date = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    # discount_policy = serializers.SerializerMethodField()
    # discount_amount = serializers.SerializerMethodField()


    def get_author(self, obj: Product):
        return obj.author.author

    def get_publisher(self, obj: Product):
        return obj.publish_info.publisher

    def get_published_date(self, obj: Product):
        return obj.publish_info.published_date.isoformat()

    # def get_discount_policy(self, obj):
        # return getattr(obj, 'discount_type', None)

    # def get_discount_amount(self, obj):
        # return getattr(obj, 'discount_amount', None)

    # def get_discount_price(self, obj):
        # return getattr(obj, 'discounted', None)
