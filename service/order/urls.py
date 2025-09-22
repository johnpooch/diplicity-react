from django.urls import path
from . import views

urlpatterns = [
    path("game/<str:game_id>/orders/<int:phase_id>", views.OrderListView.as_view(), name="order-list"),
    path("game/<str:game_id>/orders/", views.OrderCreateView.as_view(), name="order-create"),
]
