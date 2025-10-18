class AzureHealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow Azure internal IPs only for health check
        # Check the raw host header before Django validates it
        raw_host = request.META.get("HTTP_HOST", "")
        if raw_host.startswith("169.254.") and request.path == "/health/":
            # Temporarily override ALLOWED_HOSTS check
            request.META["HTTP_HOST"] = "allowed-health-check"

        return self.get_response(request)
