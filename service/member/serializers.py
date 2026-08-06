from rest_framework import serializers
from django.apps import apps
from django.db import transaction
from drf_spectacular.utils import extend_schema_field

from common.constants import GameStatus
from emit import emit

from .models import Member

ChannelMember = apps.get_model("channel", "ChannelMember")


class BaseMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    is_current_user = serializers.SerializerMethodField()
    is_bot = serializers.SerializerMethodField()
    commitment = serializers.SerializerMethodField()

    def _is_current_user(self, obj):
        if obj.user is None:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user

    def _is_bot(self, obj):
        return obj.is_bot

    def _is_masked(self, obj):
        game = self._get_game(obj)
        if not game.anonymous:
            return False
        if game.status == GameStatus.COMPLETED:
            return False
        if self._is_bot(obj):
            return False
        return not self._is_current_user(obj)

    def _get_game(self, obj):
        if "game" in self.context:
            return self.context["game"]
        return obj.game

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_user_id(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user_id

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        if self._is_masked(obj):
            return "Anonymous"
        if obj.user is None:
            return "Deleted User"
        return obj.user.profile.name

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user.profile.picture

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        return self._is_current_user(obj)

    @extend_schema_field(serializers.BooleanField)
    def get_is_bot(self, obj):
        return self._is_bot(obj)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_commitment(self, obj):
        if self._is_masked(obj):
            return None
        if obj.user is None:
            return None
        return obj.user.profile.commitment


class MemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(allow_null=True, read_only=True, source="nation.name")
    eliminated = serializers.BooleanField(read_only=True)
    kicked = serializers.BooleanField(read_only=True)
    is_game_creator = serializers.SerializerMethodField()
    nmr_extensions_remaining = serializers.IntegerField(read_only=True)
    civil_disorder = serializers.BooleanField(read_only=True)
    seeking_replacement = serializers.BooleanField(read_only=True)
    replaceable = serializers.BooleanField(read_only=True)
    removable = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField)
    def get_removable(self, obj):
        return self._get_game(obj).can_remove_member(obj)

    @extend_schema_field(serializers.BooleanField)
    def get_is_game_creator(self, obj):
        if self._is_masked(obj):
            return False
        game = self._get_game(obj)
        return obj.user_id is not None and obj.user_id == game.created_by_id

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user
        member = game.members.create(user=user)
        public_channels = game.channels.filter(private=False)
        ChannelMember.objects.bulk_create(
            [ChannelMember(member=member, channel=ch) for ch in public_channels]
        )
        return member


class MemberReplaceSerializer(serializers.Serializer):

    def create(self, validated_data):
        game = self.context["game"]
        user = self.context["request"].user

        with transaction.atomic():
            member = Member.objects.select_for_update().get(
                pk=self.context["replaced_member"].pk
            )
            if not member.replaceable:
                raise serializers.ValidationError("This seat is not open for replacement.")
            nation_name = member.nation.name if member.nation else None
            replacement = Member.objects.hand_over_seat(member, user)
            emit("seat_filled", game=game, actor=user, nation_name=nation_name)

        return replacement

    def to_representation(self, instance):
        return MemberSerializer(instance, context=self.context).data
