from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response

from common.actors import scoped
from common.views import CurrentGameMemberMixin, RefusalMixin, SelectedGameMixin

from .loaders import DrawProposalLoader
from .models import DrawProposal
from .serializers import DrawProposalOutputSerializer, VoteDrawProposalInputSerializer


class DrawProposalListView(SelectedGameMixin, CurrentGameMemberMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DrawProposalOutputSerializer

    def get_queryset(self):
        return DrawProposalLoader.get_queryset(self.request.user).for_game(self.get_game()).order_by("-created_at")


class DrawProposalCreateView(RefusalMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DrawProposalOutputSerializer

    def get_phase(self):
        phase = self.get_game().current_phase
        if phase is None:
            raise Http404
        return phase

    def perform_create(self, serializer):
        proposal = DrawProposal.objects.propose(self.get_phase(), self.request.user)
        serializer.instance = DrawProposalLoader.get(proposal.pk, self.request.user)


class DrawProposalVoteView(RefusalMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VoteDrawProposalInputSerializer

    def get_object(self):
        return get_object_or_404(scoped(DrawProposal.objects.all(), self.request.user), id=self.kwargs["proposal_id"])

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = DrawProposalLoader.get(serializer.instance.pk, request.user)
        return Response(DrawProposalOutputSerializer(instance, context=self.get_serializer_context()).data)

    def perform_update(self, serializer):
        DrawProposal.objects.vote(serializer.instance, self.request.user, **serializer.validated_data)


class DrawProposalCancelView(RefusalMixin, SelectedGameMixin, CurrentGameMemberMixin, generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DrawProposalOutputSerializer

    def get_object(self):
        return get_object_or_404(
            scoped(DrawProposal.objects.active(), self.request.user),
            id=self.kwargs["proposal_id"],
            created_by=self.get_current_game_member(),
        )

    def perform_destroy(self, instance):
        DrawProposal.objects.cancel(instance, self.request.user)
