from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .util import inline_serializer


class UnitSerializer(serializers.Serializer):
    Type = serializers.CharField(source="unit_type")
    Nation = serializers.CharField(source="nation")


class PhaseSerializer(serializers.Serializer):
    Season = serializers.CharField(source="season")
    Year = serializers.IntegerField(source="year")
    Type = serializers.CharField(source="phase_type")
    Units = inline_serializer(
        name="PhaseUnits",
        fields={
            "Type": serializers.CharField(source="unit_type"),
            "Nation": serializers.CharField(source="nation"),
            "Province": serializers.CharField(source="province"),
        },
        many=True,
    )
    SupplyCenters = inline_serializer(
        name="PhaseSupplyCenters",
        fields={
            "Province": serializers.CharField(source="province"),
            "Nation": serializers.CharField(source="nation"),
        },
        many=True,
    )
    Orders = serializers.DictField(source="orders")
    Dislodgeds = serializers.DictField(source="dislodgeds")
    Dislodgers = serializers.DictField(source="dislodgers")
    Bounces = serializers.DictField(source="bounces")
    Resolutions = serializers.DictField(source="resolutions")


class AdjudicationResponseSerializer(serializers.Serializer):
    phase = PhaseSerializer()
    options = serializers.DictField()


class GameListResponseSerializer(serializers.Serializer):

    @extend_schema_field(serializers.BooleanField())
    def get_current_user(self, obj):
        request = self.context.get("request")
        return obj.username == request.user.username

    @extend_schema_field(serializers.DictField())
    def get_actions(self, obj):
        request = self.context.get("request")
        return {
            "can_join": obj.can_join(request.user),
            "can_leave": obj.can_leave(request.user),
        }

    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    movement_phase_duration = serializers.CharField()
    actions = serializers.SerializerMethodField()

    current_phase = inline_serializer(
        name="CurrentPhase",
        fields={
            "season": serializers.CharField(),
            "year": serializers.CharField(),
            "phase_type": serializers.CharField(),
            "remaining_time": serializers.CharField(),
            "units": inline_serializer(
                name="CurrentPhaseUnits",
                fields={
                    "unit_type": serializers.CharField(),
                    "nation": serializers.CharField(),
                    "province": serializers.CharField(),
                },
                many=True,
            ),
            "supply_centers": inline_serializer(
                name="CurrentPhaseSupplyCenters",
                fields={
                    "province": serializers.CharField(),
                    "nation": serializers.CharField(),
                },
                many=True,
            ),
        },
    )
    variant = inline_serializer(
        name="Variant",
        fields={
            "id": serializers.CharField(),
            "name": serializers.CharField(),
            "description": serializers.CharField(),
            "author": serializers.CharField(),
            "nations": inline_serializer(
                name="GameVariantNations",
                fields={
                    "name": serializers.CharField(),
                    "color": serializers.CharField(),
                },
                many=True,
            ),
            "provinces": inline_serializer(
                name="GameVariantProvinces",
                fields={
                    "id": serializers.CharField(),
                    "name": serializers.CharField(),
                    "type": serializers.CharField(),
                    "supply_center": serializers.BooleanField(),
                },
                many=True,
            ),
        },
    )

    members = inline_serializer(
        name="Members",
        fields={
            "id": serializers.IntegerField(),
            "user": inline_serializer(
                name="User",
                fields={
                    "username": serializers.CharField(),
                    "current_user": serializers.SerializerMethodField(),
                    "profile": inline_serializer(
                        name="GameMemberUserProfile",
                        fields={
                            "name": serializers.CharField(),
                            "picture": serializers.CharField(),
                        },
                    ),
                },
                extra_methods={"get_current_user": get_current_user},
            ),
            "nation": serializers.CharField(),
        },
        many=True,
    )


class InlineOrdersSerializer(serializers.Serializer):
    order_type = serializers.CharField()
    source = inline_serializer(
        name="InlineOrdersSource",
        fields={
            "name": serializers.CharField(),
            "id": serializers.IntegerField(),
        },
    )
    target = inline_serializer(
        name="InlineOrdersTarget",
        fields={
            "name": serializers.CharField(),
            "id": serializers.IntegerField(),
        },
    )
    aux = inline_serializer(
        name="InlineOrdersAux",
        fields={
            "name": serializers.CharField(),
            "id": serializers.IntegerField(),
        },
    )


class GameRetrieveResponseSerializer(GameListResponseSerializer):

    @extend_schema_field(serializers.BooleanField())
    def get_current_user(self, obj):
        request = self.context.get("request")
        return obj.username == request.user.username

    @extend_schema_field(serializers.BooleanField())
    def get_orders_confirmed(self, game):
        request = self.context.get("request")
        phase_state = game.current_phase.phase_states.filter(
            member__user=request.user,
        ).first()
        if not phase_state:
            return False
        return phase_state.orders_confirmed

    orders_confirmed = serializers.SerializerMethodField()
    phases = inline_serializer(
        name="Phases",
        many=True,
        fields={
            "id": serializers.IntegerField(),
            "ordinal": serializers.IntegerField(),
            "season": serializers.CharField(),
            "year": serializers.CharField(),
            "name": serializers.CharField(),
            "phase_type": serializers.CharField(),
            "remaining_time": serializers.CharField(),
            "phase_states": inline_serializer(
                name="PhaseStates",
                fields={
                    "id": serializers.IntegerField(),
                    "member": inline_serializer(
                        name="PhaseStateMember",
                        fields={
                            "id": serializers.IntegerField(),
                            "nation": serializers.CharField(),
                            "user": inline_serializer(
                                name="PhaseStateUser",
                                fields={
                                    "username": serializers.CharField(),
                                    "current_user": serializers.SerializerMethodField(),
                                    "profile": inline_serializer(
                                        name="PhaseStateUserProfile",
                                        fields={
                                            "name": serializers.CharField(),
                                            "picture": serializers.CharField(),
                                        },
                                    ),
                                },
                                extra_methods={"get_current_user": get_current_user},
                            ),
                        },
                    ),
                    "orders": inline_serializer(
                        name="PhaseStateOrders",
                        fields={
                            "order_type": serializers.CharField(),
                            "source": serializers.CharField(),
                            "target": serializers.CharField(allow_null=True),
                            "aux": serializers.CharField(allow_null=True),
                        },
                        many=True,
                    ),
                },
                many=True,
            ),
            "units": inline_serializer(
                name="PhasesUnits",
                fields={
                    "unit_type": serializers.CharField(),
                    "nation": serializers.CharField(),
                    "province": serializers.CharField(),
                },
                many=True,
            ),
            "supply_centers": inline_serializer(
                name="PhasesSupplyCenters",
                fields={
                    "province": serializers.CharField(),
                    "nation": serializers.CharField(),
                },
                many=True,
            ),
        },
    )

    def to_representation(self, instance):
        """Override to filter phase_states based on the logged-in user."""
        representation = super().to_representation(instance)
        request = self.context.get("request")

        for phase in representation.get("phases", []):
            phase["phase_states"] = [
                phase_state
                for phase_state in phase.get("phase_states", [])
                if phase_state.get("member").get("user").get("username")
                == request.user.username
            ]

        return representation


class GameListFilterSerializer(serializers.Serializer):
    mine = serializers.BooleanField(required=False)
    can_join = serializers.BooleanField(required=False)


class GameCreateRequestSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    variant = serializers.CharField(required=True)


class LoginRequestSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.CharField()
    username = serializers.CharField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class OrderCreateRequestSerializer(serializers.Serializer):
    order_type = serializers.CharField(required=True)
    source = serializers.CharField(required=True)
    target = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    aux = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class OrderCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class PhaseStateConfirmSerializer(serializers.Serializer):
    pass


class GameLeaveRequestSerializer(serializers.Serializer):
    pass


class GameJoinRequestSerializer(serializers.Serializer):
    pass


class VariantListResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = inline_serializer(
        name="VariantNations",
        fields={
            "name": serializers.CharField(),
            "color": serializers.CharField(),
        },
        many=True,
    )
    start = inline_serializer(
        name="VariantStart",
        fields={
            "season": serializers.CharField(),
            "year": serializers.CharField(),
            "phase_type": serializers.CharField(),
            "units": inline_serializer(
                name="VariantStartUnits",
                fields={
                    "unit_type": serializers.CharField(),
                    "nation": serializers.CharField(),
                    "province": serializers.CharField(),
                },
                many=True,
            ),
            "supply_centers": inline_serializer(
                name="VariantStartSupplyCenters",
                fields={
                    "province": serializers.CharField(),
                    "nation": serializers.CharField(),
                },
                many=True,
            ),
        },
    )


class ChannelCreateRequestSerializer(serializers.Serializer):
    members = serializers.ListField(child=serializers.IntegerField(), required=True)
    id = serializers.IntegerField(required=False)


class ChannelCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class ChannelMessageCreateRequestSerializer(serializers.Serializer):
    body = serializers.CharField(required=True, max_length=1000)


class ChannelMessageCreateResponseSerializer(serializers.Serializer):
    pass


class ChannelListResponseSerializer(serializers.Serializer):

    @extend_schema_field(serializers.BooleanField())
    def get_current_user(self, obj):
        request = self.context.get("request")
        return obj.username == request.user.username

    id = serializers.IntegerField()
    name = serializers.CharField()
    private = serializers.BooleanField()
    messages = inline_serializer(
        name="ChannelMessages",
        fields={
            "id": serializers.IntegerField(),
            "body": serializers.CharField(),
            "sender": inline_serializer(
                name="MessageSender",
                fields={
                    "id": serializers.IntegerField(),
                    "nation": serializers.CharField(),
                    "user": inline_serializer(
                        name="MessageSenderUser",
                        fields={
                            "username": serializers.CharField(),
                            "current_user": serializers.SerializerMethodField(),
                            "profile": inline_serializer(
                                name="MessageSenderUserProfile",
                                fields={
                                    "name": serializers.CharField(),
                                    "picture": serializers.CharField(),
                                },
                            ),
                        },
                        extra_methods={"get_current_user": get_current_user},
                    ),
                },
            ),
            "created_at": serializers.DateTimeField(),
        },
        many=True,
    )


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    picture = serializers.CharField()
    username = serializers.CharField()
    email = serializers.CharField()
