from rest_framework.response import Response

from common.pagination import StandardPageNumberPagination


class LeaderboardPagination(StandardPageNumberPagination):
    def get_paginated_response(self, data, own=None):
        response = super().get_paginated_response(data)
        return Response({**response.data, "own": own})

    def get_paginated_response_schema(self, schema):
        paginated = super().get_paginated_response_schema(schema)
        paginated["required"] = [*paginated["required"], "own"]
        paginated["properties"]["own"] = {
            "allOf": [schema["items"]],
            "nullable": True,
        }
        return paginated
