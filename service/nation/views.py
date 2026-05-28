import gzip

from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views import View
from drf_spectacular.utils import extend_schema
from lxml import etree
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from common.constants import VariantStatus
from .models import Nation, NationFlag
from .serializers import NationFlagUploadSerializer, NationSerializer


FLAG_MAX_BYTES = 256 * 1024


class IsNationVariantOwnedDraft(permissions.BasePermission):
    message = "Only the owner of a draft variant can modify its nation flags."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.variant.status == VariantStatus.DRAFT
            and obj.variant.owner_id is not None
            and obj.variant.owner_id == request.user.id
        )


@extend_schema(
    request={"multipart/form-data": NationFlagUploadSerializer},
    responses={200: NationSerializer},
    methods=["PUT"],
)
@extend_schema(responses={204: None}, methods=["DELETE"])
class NationFlagUploadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsNationVariantOwnedDraft]
    parser_classes = [MultiPartParser]
    queryset = Nation.objects.select_related("variant")
    serializer_class = NationFlagUploadSerializer

    def get_object(self):
        nation = get_object_or_404(
            self.get_queryset(),
            variant_id=self.kwargs["variant_id"],
            nation_id=self.kwargs["nation_id"],
        )
        self.check_object_permissions(self.request, nation)
        return nation

    def put(self, request, *args, **kwargs):
        nation = self.get_object()
        upload = request.FILES.get("flag")
        if upload is None:
            return Response(
                {"flag": "No file uploaded under 'flag'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > FLAG_MAX_BYTES:
            return Response(
                {"flag": f"Flag is too large (max {FLAG_MAX_BYTES} bytes)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            text = upload.read().decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                {"flag": "Flag is not valid UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            etree.fromstring(text.encode())
        except etree.XMLSyntaxError as exc:
            return Response(
                {"flag": f"Flag could not be parsed as SVG: {exc}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            NationFlag.objects.update_or_create(nation=nation, defaults={"svg": text})

        nation.refresh_from_db()
        return Response(NationSerializer(nation, context={"request": request}).data)

    def delete(self, request, *args, **kwargs):
        nation = self.get_object()
        NationFlag.objects.filter(nation=nation).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NationFlagSvgView(View):
    def get(self, request, variant_id, nation_id, content_hash):
        try:
            flag = NationFlag.objects.get(
                nation__variant_id=variant_id,
                nation__nation_id=nation_id,
                content_hash=content_hash,
            )
        except NationFlag.DoesNotExist:
            return HttpResponseNotFound()

        body = flag.svg.encode()
        accepts_gzip = "gzip" in request.headers.get("Accept-Encoding", "")
        if accepts_gzip:
            body = gzip.compress(body)

        response = HttpResponse(body, content_type="image/svg+xml")
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        response["Vary"] = "Accept-Encoding"
        if accepts_gzip:
            response["Content-Encoding"] = "gzip"
        return response
