from django.urls import path

from .views import VariantListView, VariantSvgView

urlpatterns = [
    path("variants/", VariantListView.as_view(), name="variant-list"),
    path(
        "variants/<str:variant_id>/svg/<str:content_hash>.svg",
        VariantSvgView.as_view(),
        name="variant-svg",
    ),
]
