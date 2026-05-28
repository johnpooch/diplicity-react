import json
from typing import Optional

from django.db import transaction
from django.urls import reverse
from lxml import etree
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from nation.serializers import NationSerializer

from common.constants import VariantStatus
from .models import Variant, VariantSvg
from .utils import (
    create_variant_from_dvar,
    normalize_dsvg,
    update_variant_from_dvar,
    validate_dsvg,
    validate_dvar,
)


class VictoryConditionsSerializer(serializers.Serializer):
    solo_victory_supply_centers = serializers.IntegerField(source="soloVictorySupplyCenters")
    game_ends_year = serializers.IntegerField(source="gameEndsYear", allow_null=True)
    draw_after_year = serializers.IntegerField(source="drawAfterYear", allow_null=True)


class DominanceRuleDependencySerializer(serializers.Serializer):
    province = serializers.CharField()
    nation = serializers.CharField()


class DominanceRuleSerializer(serializers.Serializer):
    province = serializers.CharField()
    nation = serializers.CharField()
    dependencies = DominanceRuleDependencySerializer(many=True)


class VariantProvinceSlimSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)


class VariantProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
    adjacencies = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_adjacencies(self, obj):
        return [adj["to"] for adj in obj.adjacencies]


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
    owner_id = serializers.IntegerField(read_only=True, allow_null=True)
    owner_username = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    victory_conditions = VictoryConditionsSerializer(source="victory_conditions_summary")
    svg_url = serializers.SerializerMethodField()
    nations = NationSerializer(many=True)
    provinces = VariantProvinceSerializer(many=True)
    dominance_rules = serializers.SerializerMethodField()

    @extend_schema_field(DominanceRuleSerializer(many=True))
    def get_dominance_rules(self, obj):
        return obj.dominance_rules
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

    def _validate_dvar_payload(self, dvar, allow_existing_id=None):
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
        existing = Variant.objects.filter(id=dvar["id"]).first()
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
        self._validate_dvar_payload(dvar)
        user = self.context["request"].user
        with transaction.atomic():
            variant = create_variant_from_dvar(dvar, owner=user, status=VariantStatus.DRAFT)
            self._save_dsvg(variant, dsvg_text)
        return Variant.objects.with_related_data().get(id=variant.id)

    def update(self, instance, validated_data):
        dvar = self._parse_dvar(validated_data["dvar"])
        dsvg_text = self._parse_dsvg(validated_data["dsvg"])
        self._validate_dvar_payload(dvar, allow_existing_id=instance.id)
        if dvar["id"] != instance.id:
            raise serializers.ValidationError(
                {"dvar": f"DVAR id '{dvar['id']}' does not match variant id '{instance.id}'."}
            )
        with transaction.atomic():
            variant = update_variant_from_dvar(instance, dvar)
            self._save_dsvg(variant, dsvg_text)
        return Variant.objects.with_related_data().get(id=variant.id)

    def to_representation(self, instance):
        return VariantSerializer(instance, context=self.context).data


class VariantListSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    rules = serializers.CharField(allow_blank=True)
    status = serializers.CharField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True, allow_null=True)
    owner_username = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    victory_conditions = VictoryConditionsSerializer(source="victory_conditions_summary")
    svg_url = serializers.SerializerMethodField()
    nations = NationSerializer(many=True)
    provinces = VariantProvinceSlimSerializer(many=True)
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


class GameListVariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
