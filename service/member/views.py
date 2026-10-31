from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Member
from channel.models import Channel
from .serializers import (
    MemberCreateSerializer,
    MemberDetailSerializer,
    MemberJoinSerializer,
    MemberNationAssignSerializer,
    MemberNationPreferenceSerializer,
    MemberReplaceSerializer,
    MemberSerializer,
    MemberWithdrawSerializer,
)
from common.serializers import EmptySerializer
from common.constants import GameStatus
from common.permissions import (
    CanUseBotOpponent,
    IsActiveGame,
    IsActiveGamePlayer,
    IsGameMaster,
    IsGamePlayer,
    IsGameManager,
    IsMusteringGame,
    IsNotSandboxGame,
    IsUnmusteredMember,
    IsPendingGame,
    IsPendingOrActiveGame,
    IsPendingOrMusteringGame,
    IsNotGamePlayer,
    IsNotGameMaster,
    IsRemovableMember,
    IsReplaceableMember,
    IsSpaceAvailable,
    MeetsCommitmentRequirement,
)
from common.views import SeatClaimMixin, SelectedGameMixin
from emit import emit
from game.models import Game
from report.policies import CanReportPolicy


@extend_schema(responses={201: MemberSerializer})
class MemberCreateView(SeatClaimMixin, generics.CreateAPIView):
    serializer_class = MemberCreateSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingGame,
        IsGameManager,
        IsSpaceAvailable,
        CanUseBotOpponent,
    ]


@extend_schema(request=EmptySerializer, responses={201: MemberSerializer})
class MemberJoinView(SeatClaimMixin, generics.CreateAPIView):
    serializer_class = MemberJoinSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingGame,
        IsNotGamePlayer,
        IsNotGameMaster,
        IsSpaceAvailable,
        MeetsCommitmentRequirement,
    ]


class MemberRetrieveView(generics.RetrieveAPIView):
    """Retrieve one member's place in a game, including game masters and members
    who have left their seat, with the actions the requesting user can take on
    them. On the requesting user's own member, the actions are the game actions."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberDetailSerializer

    def get_object(self):
        member = get_object_or_404(
            Member.objects.with_detail_data(),
            game_id=self.kwargs["game_id"],
            id=self.kwargs["member_id"],
        )
        member.report_decision = CanReportPolicy.decide(member, self.request.user)
        return member


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingOrMusteringGame,
        IsGamePlayer,
    ]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)

    def perform_destroy(self, instance):
        game = instance.game
        user_id = instance.user_id
        with transaction.atomic():
            Channel.objects.delete_channels_left_with_one_member(instance)
            super().perform_destroy(instance)
            game.return_to_pending()
            if user_id == game.admin_id:
                game.reassign_admin()
            game.delete_if_empty_pending()


class MemberKickView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingOrActiveGame,
        IsGameManager,
        IsRemovableMember,
    ]

    def get_object(self):
        game = self.get_game()
        member = get_object_or_404(
            Member.objects.not_replaced(), game=game, id=self.kwargs["member_id"]
        )
        if member.user == self.request.user:
            self.permission_denied(
                self.request, message="Cannot kick yourself from the game."
            )
        return member

    def perform_destroy(self, instance):
        game = instance.game
        user_id = instance.user_id
        is_bot = instance.is_bot
        event_type = (
            "kicked_from_staging"
            if game.status in (GameStatus.PENDING, GameStatus.MUSTERING)
            else "removed_from_game"
        )
        with transaction.atomic():
            Member.objects.remove(instance)
            if user_id and not is_bot:
                emit(event_type, game=game, recipients=[user_id])


class MemberReplaceView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberReplaceSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsNotGamePlayer,
        IsNotGameMaster,
        IsReplaceableMember,
        MeetsCommitmentRequirement,
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["replaced_member"] = get_object_or_404(
            Member, game=self.get_game(), id=self.kwargs["member_id"]
        )
        return context

    @extend_schema(request=EmptySerializer, responses={201: MemberSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MemberMusterView(SelectedGameMixin, generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsMusteringGame,
        IsGamePlayer,
        IsUnmusteredMember,
    ]

    @extend_schema(request=EmptySerializer, responses={200: MemberSerializer})
    def post(self, request, *args, **kwargs):
        """Confirm the requesting user's seat in a mustering game."""
        game = self.get_game()
        member = get_object_or_404(Member, game=game, user=request.user)

        member.mustered_at = timezone.now()
        member.save(update_fields=["mustered_at"])

        Game.objects.arm_muster(game)

        serializer = MemberSerializer(member, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(request=None, responses={200: MemberSerializer})
class MemberWithdrawView(SelectedGameMixin, generics.UpdateAPIView):
    """Withdraw the requesting user from an active game, leaving their seat vacant for another player to claim."""

    serializer_class = MemberWithdrawSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsNotSandboxGame,
        IsActiveGamePlayer,
    ]

    def get_object(self):
        return get_object_or_404(Member, game=self.get_game(), user=self.request.user)


class MemberNationPreferenceView(SelectedGameMixin, generics.GenericAPIView):
    """Read or replace the requesting member's ranked nation preferences for a
    pending game. Array position determines rank; an empty list means no
    preference."""

    serializer_class = MemberNationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGamePlayer]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MemberNationAssignView(SelectedGameMixin, generics.GenericAPIView):
    """Pin a nation to a member of a pending game, or unpin it. Game master
    only; pinned nations are kept when the game starts."""

    serializer_class = MemberNationAssignSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMaster]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(
            Member.objects.not_replaced(), game=game, id=self.kwargs["member_id"]
        )

    @extend_schema(responses={200: MemberSerializer})
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, *args, **kwargs):
        Member.objects.clear_nation(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(exclude=True)
class CivilDisorderRecoveryView(generics.GenericAPIView):
    """Serves POST /game/<id>/recover-from-civil-disorder/ for mobile builds shipped
    before civil disorder became permanent. Kept out of the schema so codegen no
    longer emits it. Remove once those builds are out of circulation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response(
            {"detail": "Civil disorder is permanent. You cannot return to this game."},
            status=status.HTTP_410_GONE,
        )
