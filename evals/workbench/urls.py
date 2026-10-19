from django.urls import path

from workbench import views

urlpatterns = [
    path("fixtures/", views.fixture_list),
    path("fixtures/<slug:fixture_id>/", views.fixture_detail),
    path("fixtures/<slug:fixture_id>/order-set-labels/", views.order_set_labels),
    path("runs/", views.run_list),
    path("runs/<str:name>/", views.run_detail),
    path("runs/<str:name>/queue/", views.run_queue),
    path("runs/<str:name>/prompts/", views.run_prompts),
    path("runs/<str:name>/fixtures/<slug:fixture_id>/", views.run_fixture),
    path("games/", views.game_run_list),
    path("games/<str:name>/", views.game_run_detail),
    path("games/<str:name>/<int:seed>/", views.game_detail),
    path("games/<str:name>/<int:seed>/feedback/", views.game_feedback),
]
