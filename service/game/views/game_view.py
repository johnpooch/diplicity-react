from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import GameSerializer
from ..models import Game


class GameListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class QuerySerializer(serializers.Serializer):
        mine = serializers.BooleanField(required=False)
        can_join = serializers.BooleanField(required=False)

    @extend_schema(
        parameters=[QuerySerializer],
        responses={200: GameSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filters_serializer = self.QuerySerializer(data=self.request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        games = services.GameService(self.request.user).list(filters)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameRetrieveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: GameSerializer},
    )
    def get(self, request, game_id):
        game = services.GameService(request.user).retrieve(game_id)
        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class GameCreateRequestSerializer(serializers.Serializer):
        name = serializers.CharField(required=True)
        variant = serializers.CharField(required=True)
        nation_assignment = serializers.ChoiceField(
            choices=Game.NATION_ASSIGNMENT_CHOICES,
            required=False,
            default=Game.RANDOM
        )

    @extend_schema(
        request=GameCreateRequestSerializer,
        responses={201: GameSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.GameCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        game_service = services.GameService(request.user)
        game = game_service.create(validated_data)
        game = game_service.retrieve(game.id)

        response_serializer = GameSerializer(game)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class GameJoinView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class GameJoinRequestSerializer(serializers.Serializer):
        pass

    @extend_schema(
        request=GameJoinRequestSerializer,
        responses={200: GameSerializer},
    )
    def post(self, request, game_id, *args, **kwargs):
        game_service = services.GameService(request.user)

        game = game_service.join(game_id)

        if len(game.variant.nations) == game.members.count():
            # Synchronously start the game if full
            game_service.start(game.id)

        game = game_service.retrieve(game.id)
        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameLeaveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={204: None},
    )
    def delete(self, request, game_id, *args, **kwargs):
        game_service = services.GameService(request.user)
        game_service.leave(game_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GameConfirmPhaseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class GameConfirmPhaseRequestSerializer(serializers.Serializer):
        pass

    @extend_schema(
        request=GameConfirmPhaseRequestSerializer,
        responses={200: GameSerializer},
    )
    def post(self, request, game_id, *args, **kwargs):
        game_service = services.GameService(request.user)
        game_service.confirm_phase(game_id)
        game = game_service.retrieve(game_id)

        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)
