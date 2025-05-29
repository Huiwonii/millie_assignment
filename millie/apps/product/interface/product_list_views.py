from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.product.application.use_case import ProductListUseCase
from apps.product.infrastructure.persistence.repository_impl import ProductRepositoryImpl
from apps.product.interface.serializer import ProductSerializer


class ProductListView(APIView):

    def __init__(self, **kwargs):
        self.product_list_use_case = ProductListUseCase(ProductRepositoryImpl())

    def get(self, request):
        products = self.product_list_use_case.execute()
        return Response(
            ProductSerializer(products, many=True).data,
            status=status.HTTP_200_OK,
        )