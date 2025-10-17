from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def test_sentry(request):
    raise Exception("This is a test Sentry error")
