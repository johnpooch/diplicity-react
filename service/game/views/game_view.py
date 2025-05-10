from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..util import inline_serializer


class GameListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class QuerySerializer(serializers.Serializer):
        mine = serializers.BooleanField(required=False)
        can_join = serializers.BooleanField(required=False)

    class ResponseSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()
        status = serializers.CharField()
        movement_phase_duration = serializers.CharField()
        can_join = serializers.BooleanField()
        can_leave = serializers.BooleanField()
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
                        "type": serializers.CharField(),
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
                "is_current_user": serializers.BooleanField(),
                "user": inline_serializer(
                    name="User",
                    fields={
                        "username": serializers.CharField(),
                        "profile": inline_serializer(
                            name="GameMemberUserProfile",
                            fields={
                                "name": serializers.CharField(),
                                "picture": serializers.CharField(),
                            },
                        ),
                    },
                ),
                "nation": serializers.CharField(),
            },
            many=True,
        )

    @extend_schema(
        parameters=[QuerySerializer],
        responses={200: ResponseSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filters_serializer = self.QuerySerializer(data=self.request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        games = services.GameService(self.request.user).list(filters)
        serializer = self.ResponseSerializer(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameRetrieveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class ResponseSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()
        status = serializers.CharField()
        movement_phase_duration = serializers.CharField()
        can_join = serializers.BooleanField()
        can_leave = serializers.BooleanField()
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
                        "type": serializers.CharField(),
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
                "is_current_user": serializers.BooleanField(),
                "user": inline_serializer(
                    name="User",
                    fields={
                        "username": serializers.CharField(),
                        "profile": inline_serializer(
                            name="GameMemberUserProfile",
                            fields={
                                "name": serializers.CharField(),
                                "picture": serializers.CharField(),
                            },
                        ),
                    },
                ),
                "nation": serializers.CharField(),
            },
            many=True,
        )

    @extend_schema(
        responses={200: ResponseSerializer},
    )
    def get(self, request, game_id):
        game = services.GameService(request.user).retrieve(game_id)
        serializer = self.ResponseSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)
