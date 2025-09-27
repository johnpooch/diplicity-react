from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend

from .models import Game
from .serializers import GameSerializer
from .filters import GameFilter


class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer

    queryset = Game.objects.all().with_related_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))


class GameListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer
    queryset = Game.objects.all().with_related_data()
    filterset_class = GameFilter
    filter_backends = [DjangoFilterBackend]


class GameCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameSerializer
