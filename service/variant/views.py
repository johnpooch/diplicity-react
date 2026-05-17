import gzip

from django.http import HttpResponse, HttpResponseNotFound
from django.views import View
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Variant, VariantSvg
from .serializers import VariantSerializer


class VariantListView(ListAPIView):
    serializer_class = VariantSerializer
    permission_classes = [AllowAny]
    queryset = Variant.objects.all().with_related_data()


class VariantSvgView(View):
    def get(self, request, variant_id, content_hash):
        try:
            variant_svg = VariantSvg.objects.get(variant_id=variant_id, content_hash=content_hash)
        except VariantSvg.DoesNotExist:
            return HttpResponseNotFound()

        body = variant_svg.svg.encode()
        accepts_gzip = "gzip" in request.headers.get("Accept-Encoding", "")
        if accepts_gzip:
            body = gzip.compress(body)

        response = HttpResponse(body, content_type="image/svg+xml")
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        response["Vary"] = "Accept-Encoding"
        if accepts_gzip:
            response["Content-Encoding"] = "gzip"
        return response
