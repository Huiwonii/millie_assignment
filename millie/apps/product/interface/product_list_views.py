from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.product.application.product_list_use_case import ProductListUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.product.interface.serializer import ProductSerializer
from apps.utils import const


class ProductListView(APIView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product_list_use_case = ProductListUseCase(ProductRepositoryImpl())

    def get(self, request):
        try:
            products = self.product_list_use_case.execute()
        except Exception as e:
            return Response(
                {
                    const.CODE: status.HTTP_500_INTERNAL_SERVER_ERROR,
                    const.MESSAGE: str(e),
                    const.DATA: {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not products:
            return Response(
                {
                    const.CODE: status.HTTP_404_NOT_FOUND,
                    const.MESSAGE: "No products found.",
                    const.DATA: {}
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serialized_data = ProductSerializer(products, many=True).data
        return Response(
            {
                const.CODE: status.HTTP_200_OK,
                const.MESSAGE: "OK.",
                const.DATA: serialized_data,
            },
            status=status.HTTP_200_OK,
        )