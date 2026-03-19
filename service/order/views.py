from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer, OrderOptionsResponseSerializer
from .utils import flatten_options, FIELD_ORDER
from common.permissions import IsActiveGame, IsActiveGameMember
from common.views import SelectedPhaseMixin, CurrentPhaseMixin
from common.serializers import EmptySerializer


class OrderListView(SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(self.request.user, self.get_phase()).with_related_data()


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
        members = phase.game.members.filter(user=request.user)
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
