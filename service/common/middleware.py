from corsheaders.middleware import CorsMiddleware as BaseCorsMiddleware


class CorsMiddleware(BaseCorsMiddleware):
    def add_response_headers(self, request, response):
        allow_origin = response.get("Access-Control-Allow-Origin")
        response = super().add_response_headers(request, response)
        if allow_origin == "*":
            response["Access-Control-Allow-Origin"] = "*"
        return response
