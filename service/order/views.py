from rest_framework import permissions, generics, exceptions
from django.shortcuts import get_object_or_404
from django.apps import apps

from .models import Order
from .serializers import OrderSerializer
from common.permissions import IsActiveGame, IsActiveGameMember
from common.views import SelectedPhaseMixin, CurrentPhaseMixin


class OrderListView(SelectedPhaseMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.visible_to_user_in_phase(self.request.user, self.get_phase()).with_related_data()


class OrderCreateView(CurrentPhaseMixin, generics.CreateAPIView):

    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsActiveGameMember]
    serializer_class = OrderSerializer
