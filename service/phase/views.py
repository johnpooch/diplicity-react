from rest_framework import permissions, generics, views, status
from drf_spectacular.utils import extend_schema
from opentelemetry import trace
from common.permissions import (
    IsActiveGame,
    IsActiveOrCompletedGame,
    IsActiveGameMember,
    IsCurrentPhaseActive,
    IsUserPhaseStateExists,
    IsNotSandboxGame,
    IsSandboxGame,
)
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from rest_framework.response import Response
from .models import Phase
from .serializers import PhaseStateSerializer, PhaseRetrieveSerializer, PhaseListSerializer

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
        IsActiveOrCompletedGame,
    ]
    serializer_class = PhaseStateSerializer

    def get_queryset(self):
        game = self.get_game()
        current_phase = game.current_phase
        return current_phase.phase_states.filter(member__user=self.request.user)


class PhaseListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveOrCompletedGame,
    ]
    serializer_class = PhaseListSerializer

    def get_queryset(self):
        game = self.get_game()
        return Phase.objects.filter(game=game).only(
            'id', 'ordinal', 'season', 'year', 'type', 'status', 'game_id', 'variant_id'
        ).order_by('ordinal')


class PhaseRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PhaseRetrieveSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'phase_id'

    def get_queryset(self):
        return Phase.objects.with_related_data()


class PhaseResolveView(SelectedGameMixin, views.APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsCurrentPhaseActive,
        IsSandboxGame,
    ]

    @extend_schema(request=None, responses=PhaseListSerializer)
    def post(self, request, *args, **kwargs):
        game = self.get_game()
        current_phase = Phase.objects.with_related_data().get(pk=game.current_phase.pk)
        with tracer.start_as_current_span("phase.resolve_view") as span:
            span.set_attribute("phase.id", current_phase.id)
            span.set_attribute("game.id", str(game.id))
            new_phase = Phase.objects.resolve(current_phase)
        serializer = PhaseListSerializer(new_phase)
        return Response(serializer.data, status=status.HTTP_200_OK)
