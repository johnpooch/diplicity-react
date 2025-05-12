from django.shortcuts import get_object_or_404
from rest_framework import exceptions

from .. import models
from .base_service import BaseService


class OrderService(BaseService):
    def __init__(self, user):
        self.user = user

    def create(self, game_id, data):
        game = get_object_or_404(models.Game, id=game_id)

        member = game.members.filter(user=self.user).first()
        if not member:
            raise exceptions.PermissionDenied(
                detail="User is not a member of the game."
            )

        if member.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for eliminated players."
            )

        if member.kicked:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for kicked players."
            )

        if game.status != models.Game.ACTIVE:
            raise exceptions.ValidationError(
                detail="Orders can only be created for active games."
            )

        current_phase = game.current_phase
        if current_phase is None:
            raise exceptions.ValidationError(
                detail="No current phase found for the game."
            )

        current_phase_state = current_phase.phase_states.filter(
            member__user=self.user
        ).first()
        if current_phase_state.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for eliminated players."
            )

        order = models.Order.objects.create(
            phase_state=current_phase_state,
            order_type=data["order_type"],
            source=data["source"],
            target=data.get("target"),
            aux=data.get("aux"),
        )

        try:
            order.full_clean()
        except Exception as e:
            raise exceptions.ValidationError(e)

        order.save()
        return order

    def list(self, game_id, phase_id):
        game = get_object_or_404(models.Game, id=game_id)
        phase = game.phases.filter(id=phase_id).first()

        if not phase:
            raise exceptions.NotFound("Phase not found.")

        if phase.status == phase.COMPLETED:
            phase_states = phase.phase_states.all()
        else:
            phase_states = phase.phase_states.filter(member__user=self.user)

        orders = []
        for phase_state in phase_states:
            orders.extend(phase_state.orders.select_related('resolution').all())

        grouped_orders = {}
        for order in orders:
            nation = order.phase_state.member.nation
            if nation not in grouped_orders:
                grouped_orders[nation] = []
            grouped_orders[nation].append(order)

        return grouped_orders
