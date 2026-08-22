from django.urls import path

from .views import NationFlagSvgView, NationFlagUploadView

urlpatterns = [
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
