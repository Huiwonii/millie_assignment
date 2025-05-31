from apps.product.domain.entity import Product as ProductDomainEntity
from apps.product.infrastructure.persistence.models import Book as BookModel
from apps.product.infrastructure.persistence.models import BookDetail as BookDetailModel
from apps.product.infrastructure.persistence.models import BookFeature as BookFeatureModel
from apps.product.infrastructure.persistence.models import PublishInfo as PublishInfoModel
from apps.product.infrastructure.persistence.models import Author as AuthorModel


class ProductMapper:

    @staticmethod
    def to_domain(book_model: BookModel) -> ProductDomainEntity:
        return ProductDomainEntity(
            code=book_model.code,
            name=book_model.name,
            price=book_model.price,
            discount_rate=book_model.discount_rate,
            status=book_model.status,
            detail=book_model.detail if hasattr(book_model, "detail") else None,
            feature=book_model.feature.first() if hasattr(book_model, "feature") else None,  # TODO! ManyToOne
            publish_info=book_model.publish_info if hasattr(book_model, "publish_info") else None,
            author=book_model.author if hasattr(book_model, "author") else None,
            created_at=book_model.created_at,
            updated_at=book_model.updated_at,
        )

    # def to_domain(
    #     book_model: BookModel,
    #     book_detail_model: BookDetailModel,
    #     book_feature_model: BookFeatureModel,
    #     publish_info_model: PublishInfoModel,
    #     author_model: AuthorModel,
    # ) -> ProductDomainEntity:
    #     return ProductDomainEntity(
    #         code=book_model.code,
    #         name=book_model.name,
    #         price=book_model.price,
    #         discount_rate=book_model.discount_rate,
    #         status=book_model.status,
    #         detail=book_detail_model,
    #         feature=book_feature_model,
    #         publish_info=publish_info_model,
    #         author=author_model,
    #     )