from django.urls import include, path

from .views import (
    VariantDetailView,
    VariantDvarDownloadView,
    VariantListCreateView,
    VariantMineListView,
    VariantSvgView,
)

urlpatterns = [
    path("variants/", VariantListCreateView.as_view(), name="variant-list"),
    path("variants/mine/", VariantMineListView.as_view(), name="variant-mine-list"),
    path("variants/<str:pk>/", VariantDetailView.as_view(), name="variant-detail"),
    path(
        "variants/<str:variant_id>/dvar/",
        VariantDvarDownloadView.as_view(),
        name="variant-dvar",
    ),
    path(
        "variants/<str:variant_id>/svg/<str:content_hash>.svg",
        VariantSvgView.as_view(),
        name="variant-svg",
    ),
    path("", include("nation.urls")),
]
