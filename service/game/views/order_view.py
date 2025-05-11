from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import OrderSerializer


class OrderCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    class OrderCreateRequestSerializer(serializers.Serializer):
        order_type = serializers.CharField(required=True)
        source = serializers.CharField(required=True)
        target = serializers.CharField(
            required=False, allow_null=True, allow_blank=True
        )
        aux = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    @extend_schema(
        request=OrderCreateRequestSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request, game_id, *args, **kwargs):
        serializer = self.OrderCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        order_service = services.OrderService(request.user)
        order = order_service.create(game_id, validated_data)

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
