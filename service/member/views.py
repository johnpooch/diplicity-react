from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberSerializer
from common.serializers import EmptySerializer
from common.permissions import IsActiveGame, IsGameMember, IsGameManager, IsInCivilDisorder, IsPendingGame, IsNotGameMember, IsNotGameMaster, IsSpaceAvailable, MeetsCommitmentRequirement
from common.views import SelectedGameMixin
from emit import emit


class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsNotGameMaster, IsSpaceAvailable, MeetsCommitmentRequirement]

    @extend_schema(request=EmptySerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        member = serializer.save()
        member.game.start_if_full()


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

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
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameManager]

    def get_object(self):
        game = self.get_game()
        member = get_object_or_404(Member, game=game, id=self.kwargs["member_id"])
        if member.user == self.request.user:
            self.permission_denied(self.request, message="Cannot kick yourself from the game.")
        return member

    def perform_destroy(self, instance):
        game = instance.game
        user_id = instance.user_id
        is_bot = instance.user is not None and hasattr(instance.user, "bot_profile")
        with transaction.atomic():
            instance.delete()
            if user_id and not is_bot:
                emit("kicked_from_staging", game=game, recipients=[user_id])


class CivilDisorderRecoveryView(SelectedGameMixin, generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsGameMember,
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
