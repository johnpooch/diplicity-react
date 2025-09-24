from django.urls import path

from .views import VariantListView

urlpatterns = [
    path("variants/", VariantListView.as_view(), name="variant-list"),
]