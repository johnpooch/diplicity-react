from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from opentelemetry import trace

from .models import Game
from .serializers import GameSerializer, SandboxGameSerializer
from .filters import GameFilter

tracer = trace.get_tracer(__name__)


class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer

    queryset = Game.objects.all().with_related_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))


class GameListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        with tracer.start_as_current_span("view.get_queryset"):
            queryset = Game.objects.all().with_related_data()

            if "sandbox" not in self.request.query_params:
                queryset = queryset.filter(sandbox=False)

            return queryset

    def list(self, request, *args, **kwargs):
        with tracer.start_as_current_span("view.list") as span:
            queryset = self.filter_queryset(self.get_queryset())

            with tracer.start_as_current_span("view.queryset_evaluation"):
                games = list(queryset)
                span.set_attribute("games.count", len(games))

            with tracer.start_as_current_span("view.serialization"):
                serializer = self.get_serializer(games, many=True)
                data = serializer.data

            return Response(data)


class GameCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer


class CreateSandboxGameView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SandboxGameSerializer
