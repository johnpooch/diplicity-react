from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Variant
from .serializers import VariantSerializer


class VariantListView(ListAPIView):
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated]
    queryset = Variant.objects.all().with_related_data()
