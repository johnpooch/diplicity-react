from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Variant
from .serializers import VariantSerializer


@method_decorator(cache_page(60 * 60 * 24 * 30), name="dispatch")
class VariantListView(ListAPIView):
    serializer_class = VariantSerializer
    permission_classes = [IsAuthenticated]
    queryset = Variant.objects.all().with_related_data()
