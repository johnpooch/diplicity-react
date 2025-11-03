from rest_framework import permissions, generics, views, status
from opentelemetry import trace
from common.permissions import (
    IsActiveGame,
    IsActiveGameMember,
    IsCurrentPhaseActive,
    IsUserPhaseStateExists,
    IsNotSandboxGame,
    IsSandboxGame,
)
from common.serializers import EmptySerializer
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from rest_framework.response import Response
from .models import Phase
from .serializers import PhaseStateSerializer, PhaseResolveResponseSerializer, PhaseSerializer

tracer = trace.get_tracer(__name__)


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
    serializer_class = EmptySerializer

    def post(self, request, *args, **kwargs):
        with tracer.start_as_current_span("phase.resolve_all_view") as span:
            result = Phase.objects.resolve_due_phases()
            span.set_attribute("phases.resolved", result["resolved"])
            span.set_attribute("phases.failed", result["failed"])
            return Response(result, status=status.HTTP_200_OK)


class PhaseRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhaseSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'phase_id'

    def get_queryset(self):
        return Phase.objects.with_detail_data()


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
        with tracer.start_as_current_span("phase.resolve_view") as span:
            span.set_attribute("phase.id", current_phase.id)
            span.set_attribute("game.id", str(game.id))
            Phase.objects.resolve_phase(current_phase)
        return Response(status=status.HTTP_204_NO_CONTENT)
