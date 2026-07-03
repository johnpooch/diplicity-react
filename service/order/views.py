import hashlib

from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer, OrderOptionsResponseSerializer
from .utils import flatten_options, build_move_coast_lookup, FIELD_ORDER
from common.constants import PhaseStatus
from common.permissions import IsActiveGame, IsActiveGameMember
from common.views import SelectedPhaseMixin, CurrentPhaseMixin
from common.serializers import EmptySerializer


# Orders on a completed phase never change, and completed-phase visibility is
# not user-specific (visible_to_user_in_phase returns every nation's orders), so
# the response is immutable and identical across users. Cache it in the client.
COMPLETED_PHASE_ORDERS_MAX_AGE = 60 * 60 * 24 * 7  # 1 week


def _completed_phase_orders_etag(phase):
    digest = hashlib.sha256(f"orders|{phase.id}".encode()).hexdigest()
    return f'"{digest[:32]}"'


class OrderListView(SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(self.request.user, self.get_phase()).with_related_data()

    def list(self, request, *args, **kwargs):
        phase = self.get_phase()
        if phase.status == PhaseStatus.COMPLETED:
            etag = _completed_phase_orders_etag(phase)
            if request.headers.get("If-None-Match") == etag:
                response = Response(status=status.HTTP_304_NOT_MODIFIED)
            else:
                response = self._build_orders_response()
            response["ETag"] = etag
            response["Cache-Control"] = f"private, max-age={COMPLETED_PHASE_ORDERS_MAX_AGE}"
            return response
        return self._build_orders_response()

    def _build_orders_response(self):
        orders = list(self.get_queryset())
        context = self.get_serializer_context()
        context["move_coast_lookup"] = build_move_coast_lookup(orders)
        serializer = self.get_serializer(orders, many=True, context=context)
        return Response(serializer.data)


class OrderCreateView(CurrentPhaseMixin, generics.CreateAPIView):

    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = OrderSerializer


class OrderOptionsView(CurrentPhaseMixin, generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = OrderOptionsResponseSerializer

    def retrieve(self, request, *args, **kwargs):
        phase = self.get_phase()
        province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}
        transformed = phase.transformed_options or {}
        members = phase.game.members.select_related("nation").filter(user=request.user)
        nation_names = [m.nation.name for m in members]

        all_orders = []
        for nation_name in nation_names:
            nation_options = transformed.get(nation_name, {})
            all_orders.extend(flatten_options(nation_options, province_lookup))

        data = {"orders": all_orders, "field_order": FIELD_ORDER}
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class OrderDeleteView(CurrentPhaseMixin, generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = EmptySerializer

    def get_object(self):
        phase = self.get_phase()
        return get_object_or_404(
            Order,
            source__province_id=self.kwargs["source_id"],
            phase_state__member__user=self.request.user,
            phase_state__phase=phase,
        )
