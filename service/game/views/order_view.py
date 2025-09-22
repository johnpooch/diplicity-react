from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OrderableProvinceListResponseSerializer


class OrderableProvincesListView(views.APIView):
    """
    Lists the provinces that the user can order for the current phase,
    along with any existing orders for those provinces.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OrderableProvinceListResponseSerializer(many=True)},
    )
    def get(self, request, game_id, *args, **kwargs):
        order_service = services.OrderService(request.user)
        orderable_provinces = order_service.list_orderable_provinces(game_id)

        serializer = OrderableProvinceListResponseSerializer(orderable_provinces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
