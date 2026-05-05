import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game

delete_viewname = "game-delete"


class TestGameDeleteView:

    @pytest.mark.django_db
    def test_delete_sandbox_game_as_creator(self, authenticated_client, sandbox_game):
        game = sandbox_game()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Game.objects.filter(id=game.id).exists()

    @pytest.mark.django_db
    def test_delete_sandbox_game_cascades_related_data(
        self, authenticated_client, sandbox_game
    ):
        game = sandbox_game()
        phase_ids = list(game.phases.values_list("id", flat=True))
        member_ids = list(game.members.values_list("id", flat=True))

        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        from phase.models import Phase
        from member.models import Member

        assert not Phase.objects.filter(id__in=phase_ids).exists()
        assert not Member.objects.filter(id__in=member_ids).exists()

    @pytest.mark.django_db
    def test_delete_non_sandbox_game_forbidden(
        self, authenticated_client, active_game_created_by_primary_user
    ):
        url = reverse(delete_viewname, args=[active_game_created_by_primary_user.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_delete_sandbox_game_as_non_creator(
        self, authenticated_client_for_secondary_user, sandbox_game
    ):
        game = sandbox_game()
        url = reverse(delete_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Game.objects.filter(id=game.id).exists()

    @pytest.mark.django_db
    def test_delete_sandbox_game_unauthenticated(
        self, unauthenticated_client, sandbox_game
    ):
        game = sandbox_game()
        url = reverse(delete_viewname, args=[game.id])
        response = unauthenticated_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_delete_nonexistent_game(self, authenticated_client):
        url = reverse(delete_viewname, args=["nonexistent-game"])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
