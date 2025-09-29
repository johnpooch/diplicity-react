from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics

from .models import Order
from .serializers import OrderSerializer
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
