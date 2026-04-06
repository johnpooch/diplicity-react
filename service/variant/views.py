from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Variant
from .serializers import VariantSerializer


class VariantListView(ListAPIView):
    serializer_class = VariantSerializer
    permission_classes = [AllowAny]
    queryset = Variant.objects.all().with_related_data()
