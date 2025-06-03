from rest_framework import serializers

from apps.product.domain.entity import (
    Product,
)


class BookDetailSerializer(serializers.Serializer):
    category = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class BookFeatureSerializer(serializers.Serializer):
    feature = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class PublishInfoSerializer(serializers.Serializer):
    publisher = serializers.CharField()
    published_date = serializers.DateField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class AuthorSerializer(serializers.Serializer):
    author = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    author = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()
    published_date = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_author(self, obj: Product):
        return obj.author.author

    def get_publisher(self, obj: Product):
        return obj.publish_info.publisher

    def get_published_date(self, obj: Product):
        return obj.publish_info.published_date.isoformat() if obj.publish_info and obj.publish_info.published_date else None


class ProductDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    author = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()
    published_date = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    detail = BookDetailSerializer(required=False, allow_null=True)
    feature = BookFeatureSerializer(required=False, allow_null=True)
    publish_info = PublishInfoSerializer(required=False, allow_null=True)
    author = AuthorSerializer(required=False, allow_null=True)

    def get_author(self, obj: Product):
        return obj.author.author

    def get_publisher(self, obj: Product):
        return obj.publish_info.publisher

    def get_published_date(self, obj: Product):
        return obj.publish_info.published_date.isoformat() if obj.publish_info and obj.publish_info.published_date else None
