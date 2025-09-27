from rest_framework import permissions, generics, views, status
from common.permissions import IsActiveGame, IsActiveGameMember, IsCurrentPhaseActive, IsUserPhaseStateExists
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from rest_framework.response import Response
from .models import Phase
from .serializers import PhaseStateSerializer


class PhaseStateUpdateView(SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsCurrentPhaseActive,
        IsUserPhaseStateExists,
    ]
    serializer_class = PhaseStateSerializer

    def get_object(self):
        game = self.get_game()
        member = self.get_current_game_member()
        current_phase = game.current_phase
        return current_phase.phase_states.get(member=member)


class PhaseStateRetrieveView(SelectedGameMixin, CurrentGameMemberMixin, generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
    ]
    serializer_class = PhaseStateSerializer

    def get_object(self):
        game = self.get_game()
        member = self.get_current_game_member()
        current_phase = game.current_phase
        return current_phase.phase_states.get(member=member)


class PhaseResolveView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        result = Phase.objects.resolve_due_phases()
        return Response(result, status=status.HTTP_200_OK)
