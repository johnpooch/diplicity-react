import gzip
import hashlib
import json

from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse, HttpResponseNotFound
from django.views import View
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.constants import VariantStatus
from nation.models import NationFlag
from province.models import Province
from .models import Variant, VariantSvg
from .serializers import VariantSerializer, VariantWriteSerializer
from .utils import variant_to_canonical_dict


class IsOwnedDraftForWrite(permissions.BasePermission):
    message = "Only the owner of a draft variant can modify it."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.status == VariantStatus.DRAFT
            and obj.owner_id is not None
            and obj.owner_id == request.user.id
        )


def _variants_list_etag(user_id):
    variant_max = Variant.objects.aggregate(Max("updated_at"))["updated_at__max"]
    flag_max = NationFlag.objects.aggregate(Max("updated_at"))["updated_at__max"]
    digest = hashlib.sha256(
        f"{variant_max}|{flag_max}|{user_id}".encode()
    ).hexdigest()
    return f'"{digest[:32]}"'


class VariantListCreateView(generics.ListCreateAPIView):
    queryset = Variant.objects.all().with_related_data()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VariantWriteSerializer
        return VariantSerializer

    def list(self, request, *args, **kwargs):
        etag = _variants_list_etag(request.user.id)
        if request.headers.get("If-None-Match") == etag:
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        else:
            response = super().list(request, *args, **kwargs)
        response["ETag"] = etag
        response["Cache-Control"] = "private, must-revalidate, max-age=60"
        return response


class VariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Variant.objects.all().with_related_data()
    permission_classes = [IsAuthenticated, IsOwnedDraftForWrite]
    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return VariantWriteSerializer
        return VariantSerializer

    def perform_destroy(self, instance):
        with transaction.atomic():
            Province.objects.filter(variant=instance, parent__isnull=False).delete()
            instance.delete()


class VariantDvarDownloadView(generics.GenericAPIView):
    queryset = Variant.objects.all().with_related_data()
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "variant_id"

    def get(self, request, *args, **kwargs):
        variant = self.get_object()
        dvar = variant_to_canonical_dict(variant)
        body = json.dumps(dvar, indent=2)
        response = HttpResponse(body, content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="{variant.id}.dvar.json"'
        return response


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
