from rest_framework import permissions, generics, views, status
from common.permissions import (
    IsActiveGame,
    IsActiveGameMember,
    IsCurrentPhaseActive,
    IsUserPhaseStateExists,
    IsNotSandboxGame,
    IsSandboxGame,
)
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from rest_framework.response import Response
from .models import Phase
from .serializers import PhaseStateSerializer, PhaseResolveResponseSerializer


class PhaseStateUpdateView(SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsCurrentPhaseActive,
        IsUserPhaseStateExists,
        IsNotSandboxGame,
    ]
    serializer_class = PhaseStateSerializer

    def get_object(self):
        game = self.get_game()
        member = self.get_current_game_member()
        current_phase = game.current_phase
        return current_phase.phase_states.get(member=member)


class PhaseStateListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
    ]
    serializer_class = PhaseStateSerializer

    def get_queryset(self):
        game = self.get_game()
        current_phase = game.current_phase
        return current_phase.phase_states.filter(member__user=self.request.user)


class PhaseResolveAllView(views.APIView):
    permission_classes = []
    serializer_class = PhaseResolveResponseSerializer

    def post(self, request, *args, **kwargs):
        result = Phase.objects.resolve_due_phases()
        return Response(result, status=status.HTTP_200_OK)


class PhaseResolveView(SelectedGameMixin, views.APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsCurrentPhaseActive,
        IsSandboxGame,
    ]

    def post(self, request, *args, **kwargs):
        game = self.get_game()
        current_phase = game.current_phase
        Phase.objects.resolve_phase(current_phase)
        return Response(status=status.HTTP_204_NO_CONTENT)
