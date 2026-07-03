import gzip
import hashlib
import json

from django.core.cache import cache
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse, HttpResponseNotFound
from django.views import View
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.constants import VariantStatus
from nation.models import NationFlag
from province.models import Province
from .models import Variant, VariantSvg
from .serializers import VariantSerializer, VariantWriteSerializer
from .utils import variant_to_canonical_dict

# Rendered published-variant lists are cached under a key that encodes the
# content-version inputs, so entries self-invalidate whenever a variant or flag
# changes. The timeout only bounds memory for keys that are never re-requested.
_VARIANTS_LIST_CACHE_TIMEOUT = 60 * 60 * 24


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


def _variants_list_cache_inputs():
    variant_max = Variant.objects.aggregate(Max("updated_at"))["updated_at__max"]
    flag_max = NationFlag.objects.aggregate(Max("updated_at"))["updated_at__max"]
    return variant_max, flag_max


def _variants_list_etag(variant_max, flag_max, user):
    digest = hashlib.sha256(
        f"{variant_max}|{flag_max}|{user.id}".encode()
    ).hexdigest()
    return f'"{digest[:32]}"'


def _user_sees_only_published_variants(user):
    """Whether ``visible_to(user)`` returns exactly the published variants.

    True for anonymous users and for authenticated users who neither own a
    draft nor belong to a game running a non-published variant — the common
    case, and the only one whose payload can be served from the shared cache.
    Mirrors the non-published clauses of ``VariantQuerySet.visible_to``.
    """
    if not user.is_authenticated:
        return True
    return not (
        Variant.objects.filter(
            Q(status=VariantStatus.DRAFT, owner=user)
            | Q(games__members__user=user)
        )
        .exclude(status=VariantStatus.PUBLISHED)
        .exists()
    )


class VariantListCreateView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Variant.objects.visible_to(self.request.user).with_related_data()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VariantWriteSerializer
        return VariantSerializer

    def list(self, request, *args, **kwargs):
        variant_max, flag_max = _variants_list_cache_inputs()
        etag = _variants_list_etag(variant_max, flag_max, request.user)
        if request.headers.get("If-None-Match") == etag:
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
        elif _user_sees_only_published_variants(request.user):
            response = Response(self._published_variants_data(variant_max, flag_max))
        else:
            response = super().list(request, *args, **kwargs)
        response["ETag"] = etag
        response["Cache-Control"] = "private, must-revalidate, max-age=60"
        return response

    def _published_variants_data(self, variant_max, flag_max):
        digest = hashlib.sha256(f"{variant_max}|{flag_max}".encode()).hexdigest()
        cache_key = f"variants-list:published:{digest}"
        data = cache.get(cache_key)
        if data is None:
            queryset = Variant.objects.filter(
                status=VariantStatus.PUBLISHED
            ).with_related_data()
            serialized = self.get_serializer(queryset, many=True).data
            # Strip DRF's request-bound wrappers so the payload pickles cleanly.
            data = json.loads(json.dumps(serialized))
            cache.set(cache_key, data, _VARIANTS_LIST_CACHE_TIMEOUT)
        return data


class VariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwnedDraftForWrite]
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        return Variant.objects.visible_to(self.request.user).with_related_data()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return VariantWriteSerializer
        return VariantSerializer

    def perform_destroy(self, instance):
        with transaction.atomic():
            Province.objects.filter(variant=instance, parent__isnull=False).delete()
            instance.delete()


class VariantDvarDownloadView(generics.GenericAPIView):
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "variant_id"

    def get_queryset(self):
        return Variant.objects.visible_to(self.request.user).with_related_data()

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
