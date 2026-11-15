import json

from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema_field, inline_serializer
from lxml import etree
from rest_framework import serializers

from common.constants import VariantStatus
from common.serializers import AbsoluteUrlField, derived, hydrated
from nation.serializers import FlagUrlField
from .loaders import VariantLoader
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
    solo_victory_supply_centers = serializers.IntegerField(
        source="soloVictorySupplyCenters", allow_null=True
    )
    game_ends_year = serializers.IntegerField(source="gameEndsYear", allow_null=True)
    draw_after_year = serializers.IntegerField(source="drawAfterYear", allow_null=True)


class VariantNationSerializer(serializers.Serializer):
    nation_id = serializers.CharField()
    name = serializers.CharField()
    color = serializers.CharField(read_only=True)
    non_playable = serializers.BooleanField()
    flag_url = FlagUrlField(source="flag_path")
    solo_victory_supply_centers = derived(
        serializers.IntegerField(read_only=True, allow_null=True)
    )
    handicap = serializers.IntegerField(
        source="handicap.offset", read_only=True, allow_null=True
    )


@extend_schema_field(
    inline_serializer(
        name="VariantProvinceAdjacency",
        fields={"to": serializers.CharField(), "pass": serializers.CharField()},
        many=True,
    )
)
class AdjacenciesField(serializers.JSONField):
    pass


class VariantProvinceSerializer(serializers.Serializer):
    id = serializers.CharField(source="province_id")
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()
    parent_id = serializers.CharField(source="parent.province_id", allow_null=True)
    adjacencies = AdjacenciesField(read_only=True)


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
    unit_scaling = serializers.FloatField()
    status = serializers.CharField(read_only=True)
    official = serializers.BooleanField(read_only=True)
    ranked = serializers.BooleanField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True, allow_null=True)
    owner_username = derived(
        serializers.CharField(source="owner.username", read_only=True, allow_null=True)
    )
    can_edit = hydrated(serializers.BooleanField(read_only=True))
    victory_conditions = VictoryConditionsSerializer(
        source="victory_conditions_summary"
    )
    svg_url = AbsoluteUrlField(source="svg_path")
    nations = VariantNationSerializer(many=True)
    provinces = VariantProvinceSerializer(many=True)
    template_phase = VariantTemplatePhaseSerializer()

    class Meta:
        loader = VariantLoader


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
            raise serializers.ValidationError(
                {"dvar": f"DVAR is not valid JSON: {exc}."}
            )

    def _parse_dsvg(self, upload):
        try:
            text = upload.read().decode("utf-8")
        except UnicodeDecodeError:
            raise serializers.ValidationError({"dsvg": "DSVG file is not valid UTF-8."})
        try:
            return normalize_dsvg(text)
        except etree.XMLSyntaxError as exc:
            raise serializers.ValidationError(
                {"dsvg": f"DSVG could not be parsed: {exc}."}
            )

    def _validate_dvar_payload(self, dvar, allow_existing_id=None, owner=None):
        errors = validate_dvar(dvar)
        if errors:
            raise serializers.ValidationError(
                {
                    "dvar": [
                        {
                            "code": error.code,
                            "message": error.message,
                            "path": error.path,
                        }
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
        VariantSvg.objects.update_or_create(
            variant=variant, defaults={"svg": dsvg_text}
        )

    def create(self, validated_data):
        dvar = self._parse_dvar(validated_data["dvar"])
        dsvg_text = self._parse_dsvg(validated_data["dsvg"])
        user = self.context["request"].user
        self._validate_dvar_payload(dvar, owner=user)
        try:
            with transaction.atomic():
                variant = create_variant_from_dvar(
                    dvar, owner=user, status=VariantStatus.DRAFT
                )
                self._save_dsvg(variant, dsvg_text)
        except IntegrityError as exc:
            raise serializers.ValidationError({"dvar": str(exc)}) from exc
        return VariantLoader.get(variant.id, self.context["request"].user)

    def update(self, instance, validated_data):
        dvar = self._parse_dvar(validated_data["dvar"])
        dsvg_text = self._parse_dsvg(validated_data["dsvg"])
        user = self.context["request"].user
        self._validate_dvar_payload(dvar, allow_existing_id=instance.id, owner=user)
        if dvar["id"] != instance.slug:
            raise serializers.ValidationError(
                {
                    "dvar": f"DVAR id '{dvar['id']}' does not match variant id '{instance.slug}'."
                }
            )
        with transaction.atomic():
            variant = update_variant_from_dvar(instance, dvar)
            self._save_dsvg(variant, dsvg_text)
        return VariantLoader.get(variant.id, self.context["request"].user)

    def to_representation(self, instance):
        return VariantSerializer(instance, context=self.context).data
