import hashlib

from rest_framework import permissions, generics, views, status
from drf_spectacular.utils import extend_schema
from opentelemetry import trace
from common.permissions import (
    IsActiveGame,
    IsActiveGamePlayer,
    IsCurrentPhaseActive,
    IsUserPhaseStateExists,
    IsNotSandboxGame,
    IsSandboxGame,
)
from common.views import (
    CompletedPhaseCacheMixin,
    PrecomputedConditionalGetMixin,
    SelectedGameMixin,
    SelectedPhaseMixin,
    CurrentGameMemberMixin,
)
from rest_framework.response import Response
from game.models import Game
from province.models import Province
from .models import Phase
from .serializers import (
    PhaseStateSerializer,
    PhaseRetrieveSerializer,
    PhaseListSerializer,
    PhaseRevertSerializer,
)

tracer = trace.get_tracer(__name__)


class PhaseStateUpdateView(
    SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGamePlayer,
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


class PhaseStateListView(
    PrecomputedConditionalGetMixin, SelectedGameMixin, generics.ListAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhaseStateSerializer

    def get_fingerprint(self):
        game = self.get_game()
        key = "|".join(
            [
                Game.objects.retrieve_fingerprint(game.id, self.request),
                Phase.objects.phase_states_fingerprint(
                    game.current_phase, self.request.user
                ),
            ]
        )
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def get_queryset(self):
        game = self.get_game()
        current_phase = game.current_phase
        return current_phase.phase_states.filter(
            member__user=self.request.user
        ).select_related(
            "member__game",
            "member__nation",
            "member__user__profile__uploaded_picture",
        )


class PhaseListView(
    PrecomputedConditionalGetMixin, SelectedGameMixin, generics.ListAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhaseListSerializer

    def get_fingerprint(self):
        return Phase.objects.list_fingerprint(self.get_game().id)

    def get_queryset(self):
        game = self.get_game()
        return (
            Phase.objects.filter(game=game)
            .only(
                "id",
                "ordinal",
                "season",
                "year",
                "type",
                "status",
                "game_id",
                "variant_id",
            )
            .order_by("ordinal")
        )


class PhaseRetrieveView(
    CompletedPhaseCacheMixin, SelectedPhaseMixin, generics.RetrieveAPIView
):
    """Retrieve a phase with its units, supply centers and province ownership."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PhaseRetrieveSerializer
    lookup_field = "id"
    lookup_url_kwarg = "phase_id"
    completed_phase_etag_salt = "phase"

    def get_queryset(self):
        return Phase.objects.with_retrieve_data()

    def get_object(self):
        phase = super().get_object()
        phase.variant_provinces = Province.objects.cached_for_variant(phase.variant)
        return phase


class PhaseResolveView(SelectedGameMixin, views.APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGamePlayer,
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


@extend_schema(request=None, responses={200: PhaseListSerializer})
class PhaseRevertView(SelectedGameMixin, SelectedPhaseMixin, generics.UpdateAPIView):
    """Revert a sandbox game to this phase, deleting every later phase. This phase's orders are kept and their results cleared."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGamePlayer,
        IsSandboxGame,
    ]
    serializer_class = PhaseRevertSerializer

    def get_object(self):
        return self.get_phase()
