from django.urls import path

from . import views

urlpatterns = [
    path(
        "game/<str:game_id>/member/<int:member_id>/rating/",
        views.MemberRatingRetrieveView.as_view(),
        name="game-member-rating",
    ),
]
