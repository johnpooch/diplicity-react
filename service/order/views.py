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

ORDER_OPTIONS_REPRESENTATION_VERSION = 1


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

    def get_nation_names(self):
        if not hasattr(self, "_nation_names"):
            members = (
                self.get_phase()
                .game.members.players()
                .select_related("nation")
                .filter(user=self.request.user, eliminated_at__isnull=True)
            )
            self._nation_names = [m.nation.name for m in members if m.occupied]
        return self._nation_names

    def get_fingerprint(self):
        key = f"{ORDER_OPTIONS_REPRESENTATION_VERSION}|{self.get_phase().id}|{','.join(self.get_nation_names())}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def retrieve(self, request, *args, **kwargs):
        phase = self.get_phase()
        province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}
        transformed = phase.transformed_options or {}

        all_orders = []
        for nation_name in self.get_nation_names():
            nation_options = transformed.get(nation_name, {})
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
