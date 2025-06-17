from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import override_settings
from rest_framework.test import APIClient
from game import models
import json
import time

User = get_user_model()


class Command(BaseCommand):
    help = "Generate test data using API endpoints"

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def handle(self, *args, **kwargs):
        self.stdout.write("Generating test data...")
        
        self.client = APIClient()
        
        with transaction.atomic():
            models.Variant.objects.create(
                name="Italy vs Germany",
                id="italy-vs-germany",
            )
            user1 = User.objects.create_user(
                username="johnmcdowell",
                email="johnmcdowell0801@gmail.com",
            )
            models.UserProfile.objects.create(
                user=user1,
                name="John McDowell",
                picture="https://example.com/default_profile_picture.jpg",
            )

            user2 = User.objects.create_user(
                username="testdiplomacy51",
                email="testdiplomacy51@gmail.com",
            )
            models.UserProfile.objects.create(
                user=user2,
                name="Test Diplomacy",
                picture="https://example.com/default_profile_picture.jpg",
            )

        # Authenticate as user1
        self.client.force_authenticate(user=user1)
        self.stdout.write("Authenticated as user1")

        # Create Pending Game 1 (Classical)
        response = self.client.post(
            '/game/',
            json.dumps({
                'name': 'Pending Game 1',
                'variant': 'classical',
                'nation_assignment': 'ordered'
            }),
            content_type="application/json"
        )
        pending_game_1_id = response.json()['id']
        self.stdout.write(f"Created Classical game: {pending_game_1_id}")

        # Create Pending Game 2 (Italy vs Germany)
        response = self.client.post(
            '/game/',
            json.dumps({
                'name': 'Pending Game 2',
                'variant': 'italy-vs-germany',
                'nation_assignment': 'ordered'
            }),
            content_type="application/json"
        )
        pending_game_2_id = response.json()['id']
        self.stdout.write(f"Created Italy vs Germany game: {pending_game_2_id}")

        # Create Active Game 1 (Italy vs Germany)
        response = self.client.post(
            '/game/',
            json.dumps({
                'name': 'Active Game 1',
                'variant': 'italy-vs-germany',
                'nation_assignment': 'ordered'
            }),
            content_type="application/json"
        )
        active_game_1_id = response.json()['id']
        self.stdout.write(f"Created Active Game 1: {active_game_1_id}")

        # Have user2 join Active Game 1
        self.client.force_authenticate(user=user2)
        self.stdout.write("Authenticated as user2")

        self.client.post(
            f'/game/{active_game_1_id}/join/',
            content_type="application/json"
        )
        self.stdout.write("Joined Active Game 1")

        # Wait for game to become active (max 5 seconds)
        for _ in range(10):
            game = models.Game.objects.get(id=active_game_1_id)
            if game.status == models.Game.ACTIVE:
                break
            time.sleep(0.5)

        # Create orders for Active Game 1
        response = self.client.post(
            f'/game/{active_game_1_id}/order/',
            json.dumps({
                'order_type': 'Move',
                'source': 'rom',
                'target': 'ven'
            }),
            content_type="application/json"
        )
        self.stdout.write("Created orders for Active Game 1")

        self.client.force_authenticate(user=user1)
        self.client.post(
            f'/game/{active_game_1_id}/order/',
            json.dumps({
                'order_type': 'Move',
                'source': 'ber',
                'target': 'mun'
            }),
            content_type="application/json"
        )
        self.stdout.write("Created orders for Active Game 1")

        # Create Active Game 2 with resolved phase
        response = self.client.post(
            '/game/',
            json.dumps({'name': 'Active Game 2', 'variant': 'italy-vs-germany'}),
            content_type="application/json"
        )
        active_game_2_id = response.json()['id']
        self.stdout.write(f"Created Active Game 2: {active_game_2_id}")
        # Have user2 join Active Game 2
        self.client.force_authenticate(user=user2)
        self.stdout.write("Authenticated as user2")

        self.client.post(
            f'/game/{active_game_2_id}/join/',
            content_type="application/json"
        )
        self.stdout.write("Joined Active Game 2")

        # Wait for game to become active (max 5 seconds)
        for _ in range(10):
            game = models.Game.objects.get(id=active_game_2_id)
            if game.status == models.Game.ACTIVE:
                break
            time.sleep(0.5)

        # Create orders that will result in a bounce
        self.client.post(
            f'/game/{active_game_2_id}/order/',
            json.dumps({
                'order_type': 'Move',
                'source': 'rom',
                'target': 'ven'
            }),
            content_type="application/json"
        )
        self.stdout.write("Created orders for Active Game 2")

        self.client.force_authenticate(user=user1)
        self.stdout.write("Authenticated as user1")
        self.client.post(
            f'/game/{active_game_2_id}/order/',
            json.dumps({
                'order_type': 'Move',
                'source': 'mun',
                'target': 'ruh'
            }),
            content_type="application/json"
        )
        self.stdout.write("Created orders for Active Game 2")

        # Both players confirm their orders to trigger resolution
        self.client.post(
            f'/game/{active_game_2_id}/confirm/',
            content_type="application/json"
        )
        self.stdout.write("Confirmed orders for Active Game 2")

        self.client.force_authenticate(user=user2)
        self.stdout.write("Authenticated as user2")

        self.client.post(
            f'/game/{active_game_2_id}/confirm/',
            content_type="application/json"
        )
        self.stdout.write("Confirmed orders for Active Game 2")

        self.stdout.write("Test data generation complete.")
