from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Member
from .serializers import MemberSerializer
from common.serializers import EmptySerializer
from common.permissions import IsActiveGame, IsGameMember, IsInCivilDisorder, IsPendingGame, IsNotGameMember, IsSpaceAvailable
from common.views import SelectedGameMixin
import notification.utils as notification_utils


class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsPendingGame, IsNotGameMember, IsSpaceAvailable]

    @extend_schema(request=EmptySerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        member = serializer.save()
        if member.game.variant.nations.count() == member.game.members.count():
            member.game.start()


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

            user_ids = list(
                game.members.exclude(user=request.user)
                .filter(user__isnull=False)
                .values_list("user_id", flat=True)
            )
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
