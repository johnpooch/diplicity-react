from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions

from common.views import (
    ActionView,
    CreateActionView,
    CurrentGameMemberMixin,
    LoaderListView,
    SelectedGameMixin,
)

from .models import DrawProposal
from .serializers import DrawProposalOutputSerializer, VoteDrawProposalInputSerializer


class DrawProposalListView(SelectedGameMixin, CurrentGameMemberMixin, LoaderListView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DrawProposalOutputSerializer

    def get_queryset(self):
        proposals = super().get_queryset().for_game(self.get_game())
        return proposals.in_started_games().order_by("-created_at")


@extend_schema(request=DrawProposalOutputSerializer)
class DrawProposalCreateView(
    SelectedGameMixin, CurrentGameMemberMixin, CreateActionView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DrawProposalOutputSerializer

    def perform(self):
        return DrawProposal.objects.propose(self.get_game(), self.request.user)


@extend_schema_view(
    put=extend_schema(responses=VoteDrawProposalInputSerializer),
    patch=extend_schema(
        request=VoteDrawProposalInputSerializer(partial=True),
        responses=VoteDrawProposalInputSerializer,
    ),
)
class DrawProposalVoteView(SelectedGameMixin, CurrentGameMemberMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["put", "patch", "options"]
    queryset = DrawProposal.objects.all()
    lookup_url_kwarg = "proposal_id"
    input_serializer_class = VoteDrawProposalInputSerializer
    serializer_class = DrawProposalOutputSerializer

    def get_queryset(self):
        return super().get_queryset().for_game(self.get_game())

    def perform(self, proposal, accepted):
        return DrawProposal.objects.vote(proposal, self.request.user, accepted)


class DrawProposalCancelView(SelectedGameMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["delete", "options"]
    queryset = DrawProposal.objects.all()
    lookup_url_kwarg = "proposal_id"
    serializer_class = DrawProposalOutputSerializer

    def get_queryset(self):
        return super().get_queryset().for_game(self.get_game())

    def perform(self, proposal):
        return DrawProposal.objects.cancel(proposal, self.request.user)
