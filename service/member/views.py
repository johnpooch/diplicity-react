from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberCreateSerializer, MemberJoinSerializer, MemberNationAssignSerializer, MemberNationPreferenceSerializer, MemberReplaceSerializer, MemberSerializer
from common.serializers import EmptySerializer
from common.constants import GameStatus
from common.permissions import CanUseBotOpponent, IsActiveGame, IsGameMaster, IsGameMember, IsGameManager, IsInCivilDisorder, IsNotKickedGameMember, IsPendingGame, IsPendingOrActiveGame, IsPendingOrMusteringGame, IsNotGameMember, IsNotGameMaster, IsRemovableMember, IsReplaceableMember, IsSpaceAvailable, MeetsCommitmentRequirement
from common.views import SeatClaimMixin, SelectedGameMixin
from emit import emit


@extend_schema(responses={201: MemberSerializer})
class MemberCreateView(SeatClaimMixin, generics.CreateAPIView):
    serializer_class = MemberCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameManager, IsSpaceAvailable, CanUseBotOpponent]


@extend_schema(request=EmptySerializer, responses={201: MemberSerializer})
class MemberJoinView(SeatClaimMixin, generics.CreateAPIView):
    serializer_class = MemberJoinSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsNotGameMaster, IsSpaceAvailable, MeetsCommitmentRequirement]


@extend_schema(exclude=True)
class LegacyMemberJoinView(MemberJoinView):
    """Serves POST /game/<id>/join/ for mobile builds shipped before the seating
    endpoints moved under /member/. Kept out of the schema so codegen only ever
    emits the current path. Remove once those builds are out of circulation."""


@extend_schema(exclude=True)
class LegacyMemberCreateView(MemberCreateView):
    """Serves POST /game/<id>/add-bot/ for mobile builds shipped before the
    seating endpoints moved under /member/. Kept out of the schema so codegen
    only ever emits the current path. Remove once those builds are out of
    circulation."""


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingOrMusteringGame, IsGameMember]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)

    def perform_destroy(self, instance):
        game = instance.game
        user_id = instance.user_id
        with transaction.atomic():
            super().perform_destroy(instance)
            if user_id == game.admin_id:
                game.reassign_admin()
            game.delete_if_empty_pending()


class MemberKickView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingOrActiveGame, IsGameManager, IsRemovableMember]

    def get_object(self):
        game = self.get_game()
        member = get_object_or_404(Member.objects.not_replaced(), game=game, id=self.kwargs["member_id"])
        if member.user == self.request.user:
            self.permission_denied(self.request, message="Cannot kick yourself from the game.")
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
        IsNotGameMember,
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


class MemberNationPreferenceView(SelectedGameMixin, generics.GenericAPIView):
    """Read or replace the requesting member's ranked nation preferences for a
    pending game. Array position determines rank; an empty list means no
    preference."""

    serializer_class = MemberNationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

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
        return get_object_or_404(Member.objects.not_replaced(), game=game, id=self.kwargs["member_id"])

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


class CivilDisorderRecoveryView(SelectedGameMixin, generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsNotKickedGameMember,
        IsInCivilDisorder,
    ]

    @extend_schema(request=EmptySerializer, responses={200: MemberSerializer})
    def post(self, request, *args, **kwargs):
        game = self.get_game()
        member = get_object_or_404(Member, game=game, user=request.user)

        with transaction.atomic():
            member.civil_disorder = False
            member.save(update_fields=["civil_disorder"])

            current_phase = game.current_phase
            if current_phase:
                current_phase.phase_states.filter(member=member).update(
                    orders_confirmed=False
                )

            emit("civil_disorder_recovery", game=game, actor=request.user)

        serializer = MemberSerializer(member, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)
