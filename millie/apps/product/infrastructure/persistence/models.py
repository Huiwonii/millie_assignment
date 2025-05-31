from django.db import models
from apps.product.domain.value_objects import (
    Feature,
    Category,
    ProductStatus,
    VisibilityStatus,
)


class Book(models.Model):
    code = models.CharField(max_length=255, unique=True, null=False, db_comment="상품 코드")
    name = models.CharField(max_length=255, null=False, db_comment="상품명")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, db_comment="가격")
    discount_rate = models.DecimalField(max_digits=10, decimal_places=2, null=False, db_comment="할인율")
    status = models.CharField(max_length=255, choices=ProductStatus.choices(),null=False, db_comment="판매 상태")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "books"
        db_table_comment = "도서 테이블"


class BookDetail(models.Model):
    book_code = models.OneToOneField(Book, to_field="code", on_delete=models.CASCADE, db_comment="상품 코드", related_name="detail")
    category = models.CharField(max_length=255, choices=Category.choices(), null=False, db_comment="분야")
    description = models.TextField(db_comment="상품 설명")
    status = models.CharField(max_length=255, choices=VisibilityStatus.choices(), null=False, db_comment="노출 상태")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "book_details"
        db_table_comment = "도서 상세 테이블"


class BookFeature(models.Model):
    book_code = models.ForeignKey(Book, to_field="code", on_delete=models.CASCADE, db_comment="상품 코드", related_name="feature")
    feature = models.CharField(max_length=255, choices=Feature.choices(), null=False, db_comment="도서 타입")
    status = models.CharField(max_length=255, choices=VisibilityStatus.choices(), null=False, db_comment="노출 상태")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "product_features"
        db_table_comment = "도서 타입 테이블"


class PublishInfo(models.Model):
    book_code = models.OneToOneField(Book, to_field="code", on_delete=models.CASCADE, db_comment="상품 코드", related_name="publish_info")
    publisher = models.CharField(max_length=255, null=False, db_comment="출판사명")
    published_date = models.DateField(db_comment="출간일")
    status = models.CharField(max_length=255, choices=VisibilityStatus.choices(), null=False, db_comment="노출 상태")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "publishers"
        db_table_comment = "출판사 테이블"


class Author(models.Model):
    book_code = models.OneToOneField(Book, to_field="code", on_delete=models.CASCADE, db_comment="상품 코드", related_name="author")
    author = models.CharField(max_length=255, null=False, db_comment="저자명")
    status = models.CharField(max_length=255, choices=VisibilityStatus.choices(), null=False, db_comment="노출 상태")
    created_at = models.DateTimeField(auto_now_add=True, null=False, db_comment="등록 일자")
    updated_at = models.DateTimeField(auto_now=True, db_comment="수정 일자")

    class Meta:
        db_table = "authors"
        db_table_comment = "저자 테이블"