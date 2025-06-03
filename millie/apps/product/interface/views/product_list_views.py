from rest_framework import status
from rest_framework.views import APIView

from apps.product.application.get_product_list_use_case import GetProductListUseCase
from apps.product.infrastructure.persistence.product_repo_impl import ProductRepoImpl
from apps.product.interface.serializer import ProductSerializer

from apps.utils import messages
from apps.utils.exceptions import NotFoundException
from apps.utils.response import build_api_response


class ProductListView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product_list_use_case = GetProductListUseCase(ProductRepoImpl())

    def get(self, request):
        try:
            products = self.product_list_use_case.execute()
        except NotFoundException as e:
            return build_api_response(
                data=[],
                message=messages.NOT_FOUND,
                code=status.HTTP_404_NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:                # NOTE! 실제 서비스에서는 이렇게 예외처리 하지 않고 더 세밀히 해야함
            return build_api_response(
                data=[],
                message=f"{messages.INTERNAL_SERVER_ERROR}: {str(e)}",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not products:
            return build_api_response(
                data=[],
                message=messages.NOT_FOUND,
                code=status.HTTP_404_NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND,
            )

        serialized_data = ProductSerializer(products, many=True).data
        return build_api_response(
            data=serialized_data,
            message=messages.OK,
            code=status.HTTP_200_OK,
            http_status=status.HTTP_200_OK,
        )
