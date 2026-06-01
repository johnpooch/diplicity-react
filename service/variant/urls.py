from django.urls import path

from nation.views import NationFlagSvgView, NationFlagUploadView

from .views import (
    VariantDetailView,
    VariantDvarDownloadView,
    VariantListCreateView,
    VariantSvgView,
)

urlpatterns = [
    path("variants/", VariantListCreateView.as_view(), name="variant-list"),
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
    path(
        "variants/<str:variant_id>/nations/<str:nation_id>/flag/<str:content_hash>.svg",
        NationFlagSvgView.as_view(),
        name="nation-flag-svg",
    ),
    path(
        "variants/<str:variant_id>/nations/<str:nation_id>/flag/",
        NationFlagUploadView.as_view(),
        name="nation-flag",
    ),
]
