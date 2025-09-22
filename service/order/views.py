from rest_framework import permissions, generics, exceptions, serializers
from django.shortcuts import get_object_or_404
from django.apps import apps

from .models import Order
from .serializers import OrderSerializer

Game = apps.get_model("game", "Game")
Phase = apps.get_model("game", "Phase")


class SelectedPhaseMixin:
    def get_phase(self):
        game_id = self.kwargs.get("game_id")
        phase_id = self.kwargs.get("phase_id")
        return get_object_or_404(Phase, id=phase_id, game_id=game_id)


class CurrentPhaseMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        game_id = self.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        context["phase"] = game.current_phase
        return context


class OrderListView(SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(self.request.user, self.get_phase()).with_related_data()


class OrderCreateView(CurrentPhaseMixin, generics.CreateAPIView):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def check_permissions(self, request):
        super().check_permissions(request)
        game = get_object_or_404(Game, id=self.kwargs["game_id"])
        member = game.members.select_related("user").filter(user=request.user).first()

        if not member:
            raise exceptions.PermissionDenied("User is not a member of the game.")

        if member.eliminated:
            raise exceptions.PermissionDenied("Cannot create orders for eliminated players.")

        if member.kicked:
            raise exceptions.PermissionDenied("Cannot create orders for kicked players.")

        if game.status != Game.ACTIVE:
            raise exceptions.PermissionDenied("Cannot create orders for inactive games.")
