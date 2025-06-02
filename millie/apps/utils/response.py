from typing import (
    Optional,
    Union,
)

from rest_framework.response import Response
from rest_framework import status as http_status_codes


def build_api_response(
    *,
    data: Optional[Union[dict, list]] = None,
    message: str = "OK",
    code: int = 200,
    http_status: int = http_status_codes.HTTP_200_OK
) -> Response:

    payload = {
        "code": code,
        "message": message,
        "data": data if data is not None else {},
    }
    return Response(payload, status=http_status)
