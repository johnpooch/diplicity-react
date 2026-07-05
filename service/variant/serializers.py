import json
from typing import Optional

from django.db import IntegrityError, transaction
from django.urls import reverse
from drf_spectacular.utils import extend_schema_field, inline_serializer
from lxml import etree
from rest_framework import serializers
from nation.serializers import NationSerializer

from common.constants import VariantStatus
from .models import Variant, VariantSvg
from .utils import (
    create_variant_from_dvar,
    normalize_dsvg,
    update_variant_from_dvar,
    validate_dsvg,
    validate_dvar,
    variant_id_for,
)


class VictoryConditionsSerializer(serializers.Serializer):
    solo_victory_supply_centers = serializers.IntegerField(source="soloVictorySupplyCenters")
    game_ends_year = serializers.IntegerField(source="gameEndsYear", allow_null=True)
    draw_after_year = serializers.IntegerField(source="drawAfterYear", allow_null=True)


class VariantProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)
    adjacencies = serializers.SerializerMethodField()

    @extend_schema_field(
        inline_serializer(
            name="VariantProvinceAdjacency",
            fields={"to": serializers.CharField(), "pass": serializers.CharField()},
            many=True,
        )
    )
    def get_adjacencies(self, obj):
        return obj.adjacencies


class VariantTemplateNationRefSerializer(serializers.Serializer):
    name = serializers.CharField()


class VariantTemplateProvinceRefSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")


class VariantTemplateUnitSerializer(serializers.Serializer):
    type = serializers.CharField()
    dislodged = serializers.BooleanField()
    nation = VariantTemplateNationRefSerializer()
    province = VariantTemplateProvinceRefSerializer()


class VariantTemplateSupplyCenterSerializer(serializers.Serializer):
    nation = VariantTemplateNationRefSerializer()
    province = VariantTemplateProvinceRefSerializer()


class VariantTemplatePhaseSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    units = VariantTemplateUnitSerializer(many=True)
    supply_centers = VariantTemplateSupplyCenterSerializer(many=True)


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    rules = serializers.CharField(allow_blank=True)
    status = serializers.CharField(read_only=True)
    official = serializers.BooleanField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True, allow_null=True)
    owner_username = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    victory_conditions = VictoryConditionsSerializer(source="victory_conditions_summary")
    svg_url = serializers.SerializerMethodField()
    nations = NationSerializer(many=True)
    provinces = VariantProvinceSerializer(many=True)
    template_phase = VariantTemplatePhaseSerializer()

    def get_svg_url(self, variant) -> Optional[str]:
        try:
            variant_svg = variant.svg
        except VariantSvg.DoesNotExist:
            return None
        path = reverse(
            "variant-svg",
            kwargs={"variant_id": variant.id, "content_hash": variant_svg.content_hash},
        )
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path

    def get_owner_username(self, variant) -> Optional[str]:
        return variant.owner.username if variant.owner_id else None

    def get_can_edit(self, variant) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return variant.status == VariantStatus.DRAFT and variant.owner_id == request.user.id


class VariantWriteSerializer(serializers.Serializer):
    dvar = serializers.FileField(write_only=True)
    dsvg = serializers.FileField(write_only=True)

    def _parse_dvar(self, upload):
        try:
            text = upload.read().decode("utf-8")
        except UnicodeDecodeError:
            raise serializers.ValidationError({"dvar": "DVAR file is not valid UTF-8."})
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise serializers.ValidationError({"dvar": f"DVAR is not valid JSON: {exc}."})

    def _parse_dsvg(self, upload):
        try:
            text = upload.read().decode("utf-8")
        except UnicodeDecodeError:
            raise serializers.ValidationError({"dsvg": "DSVG file is not valid UTF-8."})
        try:
            return normalize_dsvg(text)
        except etree.XMLSyntaxError as exc:
            raise serializers.ValidationError({"dsvg": f"DSVG could not be parsed: {exc}."})

    def _validate_dvar_payload(self, dvar, allow_existing_id=None, owner=None):
        errors = validate_dvar(dvar)
        if errors:
            raise serializers.ValidationError(
                {
                    "dvar": [
                        {"code": error.code, "message": error.message, "path": error.path}
                        for error in errors
                    ]
                }
            )
        computed_id = variant_id_for(owner, dvar["id"])
        existing = Variant.objects.filter(id=computed_id).first()
        if existing is not None and existing.id != allow_existing_id:
            raise serializers.ValidationError(
                {"dvar": f"A variant with id '{dvar['id']}' already exists."}
            )

    def _save_dsvg(self, variant, dsvg_text):
        svg_errors = validate_dsvg(dsvg_text, variant)
        if svg_errors:
            raise serializers.ValidationError(
                {
                    "dsvg": [
                        {"code": error.code, "message": error.message}
                        for error in svg_errors
                    ]
                }
            )
        VariantSvg.objects.update_or_create(variant=variant, defaults={"svg": dsvg_text})

    def create(self, validated_data):
        dvar = self._parse_dvar(validated_data["dvar"])
        dsvg_text = self._parse_dsvg(validated_data["dsvg"])
        user = self.context["request"].user
        self._validate_dvar_payload(dvar, owner=user)
        try:
            with transaction.atomic():
                variant = create_variant_from_dvar(dvar, owner=user, status=VariantStatus.DRAFT)
                self._save_dsvg(variant, dsvg_text)
        except IntegrityError as exc:
            raise serializers.ValidationError({"dvar": str(exc)}) from exc
        return Variant.objects.with_related_data().get(id=variant.id)

    def update(self, instance, validated_data):
        dvar = self._parse_dvar(validated_data["dvar"])
        dsvg_text = self._parse_dsvg(validated_data["dsvg"])
        user = self.context["request"].user
        self._validate_dvar_payload(dvar, allow_existing_id=instance.id, owner=user)
        if dvar["id"] != instance.slug:
            raise serializers.ValidationError(
                {"dvar": f"DVAR id '{dvar['id']}' does not match variant id '{instance.slug}'."}
            )
        with transaction.atomic():
            variant = update_variant_from_dvar(instance, dvar)
            self._save_dsvg(variant, dsvg_text)
        return Variant.objects.with_related_data().get(id=variant.id)

    def to_representation(self, instance):
        return VariantSerializer(instance, context=self.context).data
