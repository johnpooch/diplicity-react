import hashlib

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, serializers
from rest_framework.response import Response

from phase.models import Phase
from .models import Order
from .serializers import OrderSerializer, OrderOptionsResponseSerializer
from .utils import flatten_options, build_move_coast_lookup, FIELD_ORDER
from common.permissions import IsActiveGame, IsActiveGamePlayer, IsCurrentPhaseActive
from common.views import (
    CompletedPhaseCacheMixin,
    CurrentPhaseMixin,
    PrecomputedConditionalGetMixin,
    SelectedPhaseMixin,
)
from common.serializers import EmptySerializer

ORDER_OPTIONS_REPRESENTATION_VERSION = 2


class OrderListView(CompletedPhaseCacheMixin, SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    completed_phase_etag_salt = "orders"

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(
            self.request.user, self.get_phase()
        ).with_related_data()

    def list(self, request, *args, **kwargs):
        orders = list(self.get_queryset())
        context = self.get_serializer_context()
        context["move_coast_lookup"] = build_move_coast_lookup(orders)
        serializer = self.get_serializer(orders, many=True, context=context)
        return Response(serializer.data)


class OrderCreateView(CurrentPhaseMixin, generics.CreateAPIView):

    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGamePlayer,
        IsCurrentPhaseActive,
    ]
    serializer_class = OrderSerializer


class OrderOptionsView(
    PrecomputedConditionalGetMixin, CurrentPhaseMixin, generics.RetrieveAPIView
):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame]
    serializer_class = OrderOptionsResponseSerializer

    def get_phase(self):
        if not hasattr(self, "_phase"):
            self._phase = super().get_phase()
        return self._phase

    def get_phase_states(self):
        if not hasattr(self, "_phase_states"):
            phase = self.get_phase()
            members = (
                phase.game.members.players()
                .select_related("nation")
                .filter(user=self.request.user, eliminated_at__isnull=True)
            )
            member_ids = [m.id for m in members if m.occupied]
            self._phase_states = list(
                phase.phase_states.select_related("member__nation", "phase")
                .filter(member_id__in=member_ids)
                .order_by("member__nation__name")
            )
        return self._phase_states

    def get_limited_sources(self):
        if not hasattr(self, "_limited_sources"):
            self._limited_sources = {
                phase_state.id: sorted(phase_state.ordered_source_province_ids())
                for phase_state in self.get_phase_states()
                if phase_state.adjustment_limit_reached()
            }
        return self._limited_sources

    def get_fingerprint(self):
        limited_sources = self.get_limited_sources()
        nations = ",".join(
            f"{phase_state.member.nation.name}:{'+'.join(limited_sources[phase_state.id])}"
            if phase_state.id in limited_sources
            else phase_state.member.nation.name
            for phase_state in self.get_phase_states()
        )
        key = f"{ORDER_OPTIONS_REPRESENTATION_VERSION}|{self.get_phase().id}|{nations}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def retrieve(self, request, *args, **kwargs):
        phase = self.get_phase()
        province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}
        transformed = phase.transformed_options or {}
        limited_sources = self.get_limited_sources()

        all_orders = []
        for phase_state in self.get_phase_states():
            nation_options = transformed.get(phase_state.member.nation.name, {})
            if phase_state.id in limited_sources:
                nation_options = {
                    source: options
                    for source, options in nation_options.items()
                    if source in limited_sources[phase_state.id]
                }
            all_orders.extend(flatten_options(nation_options, province_lookup))

        data = {"orders": all_orders, "field_order": FIELD_ORDER}
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class OrderDeleteView(CurrentPhaseMixin, generics.DestroyAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsActiveGamePlayer,
        IsCurrentPhaseActive,
    ]
    serializer_class = EmptySerializer

    def get_object(self):
        phase = self.get_phase()
        return get_object_or_404(
            Order.objects.select_related("phase_state"),
            source__province_id=self.kwargs["source_id"],
            phase_state__member__user=self.request.user,
            phase_state__phase=phase,
        )

    def perform_destroy(self, instance):
        with transaction.atomic():
            if Phase.objects.lock_if_active(instance.phase_state.phase_id) is None:
                raise serializers.ValidationError(IsCurrentPhaseActive.message)
            instance.delete()
