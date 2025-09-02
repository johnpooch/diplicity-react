from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OrderSerializer, OrderListResponseSerializer, OrderableProvinceListResponseSerializer, InteractiveOrderCreateRequestSerializer, InteractiveOrderCreateResponseSerializer


class OrderListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OrderListResponseSerializer(many=True)},
    )
    def get(self, request, game_id, phase_id, *args, **kwargs):
        order_service = services.OrderService(request.user)
        grouped_orders = order_service.list(game_id, phase_id)

        serialized_data = [
            {"nation": nation, "orders": OrderSerializer(orders, many=True).data}
            for nation, orders in grouped_orders.items()
        ]

        return Response(serialized_data, status=status.HTTP_200_OK)


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


class InteractiveOrderCreateView(views.APIView):
    """
    Interactive order creation endpoint for progressive order building.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=InteractiveOrderCreateRequestSerializer,
        responses={200: InteractiveOrderCreateResponseSerializer},
    )
    def post(self, request, game_id, *args, **kwargs):
        serializer = InteractiveOrderCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected_array = serializer.validated_data["selected"]

        order_service = services.OrderService(request.user)
        result = order_service.create_interactive(game_id, selected_array)

        response_serializer = InteractiveOrderCreateResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
