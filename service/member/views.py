from datetime import timedelta

from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberSerializer
from common.serializers import EmptySerializer
from common.permissions import IsActiveGame, IsGameMember, IsGameManager, IsInCivilDisorder, IsPendingGame, IsNotGameMember, IsNotGameMaster, IsSpaceAvailable
from common.views import SelectedGameMixin
import notification.utils as notification_utils
from notification.tasks import send_notification


class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsNotGameMaster, IsSpaceAvailable]

    def perform_create(self, serializer):
        member = serializer.save()
        game = member.game
        if game.variant.nations.count() == game.members.count():
            if game.confirmation_required:
                phase_duration = game.get_phase_duration_seconds(game.current_phase.type) if game.current_phase else None
                if phase_duration:
                    game.confirmation_deadline = timezone.now() + timedelta(seconds=phase_duration)
                else:
                    game.confirmation_deadline = timezone.now() + timedelta(hours=24)
                game.save(update_fields=["confirmation_deadline"])
            else:
                game.start()


class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)

    def perform_destroy(self, instance):
        game = instance.game
        with transaction.atomic():
            super().perform_destroy(instance)
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
        with transaction.atomic():
            instance.delete()
            if user_id:
                send_notification.defer(
                    user_ids=[user_id],
                    title=game.name,
                    body=f"You were removed from this game by {game.manager_label}.",
                    notification_type="kicked_from_staging",
                    data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
                )


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

            user_ids = game.notification_user_ids(exclude_user_id=request.user.id)
            nation_name = member.nation.name if member.nation else "A player"

            def send_notifications():
                notification_utils.send_notification_to_users(
                    user_ids=user_ids,
                    title="Player Returned",
                    body=f"{nation_name} has returned from civil disorder.",
                    notification_type="civil_disorder_recovery",
                    data={"game_id": str(game.id)},
                )

            transaction.on_commit(send_notifications)

        serializer = MemberSerializer(member, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)


class MemberConfirmView(SelectedGameMixin, generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsGameMember]

    def post(self, request, *args, **kwargs):
        game = self.get_game()
        member = get_object_or_404(Member, game=game, user=request.user)

        if not game.confirmation_required:
            return Response(
                {"detail": "This game does not require confirmation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if member.confirmed:
            return Response(
                {"detail": "Already confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.confirmed = True
        member.save(update_fields=["confirmed"])

        all_slots_filled = game.members.count() == game.variant.nations.count()
        all_confirmed = not game.members.filter(confirmed=False).exists()

        if all_slots_filled and all_confirmed:
            game.start()

        return Response(status=status.HTTP_204_NO_CONTENT)
