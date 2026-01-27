from rest_framework import permissions, generics
from django.shortcuts import get_object_or_404
from common.permissions import (
    IsActiveGame,
    IsActiveOrCompletedGame,
    IsActiveGameMember,
    IsNotSandboxGame,
)
from common.views import SelectedGameMixin, CurrentGameMemberMixin
from .models import DrawProposal
from .serializers import DrawProposalSerializer, DrawVoteUpdateSerializer


class DrawProposalListView(SelectedGameMixin, CurrentGameMemberMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveOrCompletedGame]
    serializer_class = DrawProposalSerializer

    def get_queryset(self):
        game = self.get_game()
        current_phase = game.current_phase
        return DrawProposal.objects.active().filter(
            game=game,
            phase=current_phase,
        ).with_related_data()


class DrawProposalCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsNotSandboxGame,
    ]
    serializer_class = DrawProposalSerializer


class DrawProposalVoteView(SelectedGameMixin, CurrentGameMemberMixin, generics.UpdateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsNotSandboxGame,
    ]
    serializer_class = DrawVoteUpdateSerializer

    def get_object(self):
        game = self.get_game()
        proposal_id = self.kwargs.get("proposal_id")
        return get_object_or_404(
            DrawProposal.objects.with_related_data(),
            id=proposal_id,
            game=game,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["proposal"] = self.get_object()
        return context

    def update(self, request, *args, **kwargs):
        from rest_framework.response import Response

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.refresh_from_db()
        response_serializer = DrawProposalSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(response_serializer.data)


class DrawProposalCancelView(SelectedGameMixin, CurrentGameMemberMixin, generics.DestroyAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGameMember,
        IsNotSandboxGame,
    ]
    serializer_class = DrawProposalSerializer

    def get_object(self):
        game = self.get_game()
        current_member = self.get_current_game_member()
        proposal_id = self.kwargs.get("proposal_id")
        return get_object_or_404(
            DrawProposal,
            id=proposal_id,
            game=game,
            created_by=current_member,
            cancelled=False,
        )

    def perform_destroy(self, instance):
        instance.cancelled = True
        instance.save()
