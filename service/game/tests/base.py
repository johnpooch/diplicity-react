from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from game import models

User = get_user_model()


class BaseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = models.Variant.objects.create(
            id="classical",
            name="Classical",
        )

    def create_user(self, username, password):
        user = User.objects.create_user(username=username, password=password)
        models.UserProfile.objects.create(user=user, name="Test User", picture="")
        return user

    def create_game(self, user, game_name, **kwargs):
        game = models.Game.objects.create(
            name=game_name,
            variant=self.variant,
            **kwargs,
        )
        game.members.create(user=user)

        phase = game.phases.create(
            season=self.variant.start["season"],
            year=self.variant.start["year"],
            type=self.variant.start["type"],
        )

        for unit_data in self.variant.start["units"]:
            phase.units.create(
                type=unit_data["type"],
                nation=unit_data["nation"],
                province=unit_data["province"],
            )

        for sc_data in self.variant.start["supply_centers"]:
            phase.supply_centers.create(
                nation=sc_data["nation"],
                province=sc_data["province"],
            )

        return game
