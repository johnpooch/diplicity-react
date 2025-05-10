from django.core.management.base import BaseCommand
from game import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Generate test data using Django models"

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating test data...")

        # Create Variants
        classical_variant = models.Variant.objects.create(
            name="Classical",
            id="classical",
        )
        italy_vs_germany_variant = models.Variant.objects.create(
            name="Italy vs Germany",
            id="italy-vs-germany",
        )

        # Create Users and Profiles
        user1 = User.objects.create_user(
            username="johnmcdowell",
            email="johnmcdowell0801@gmail.com",
        )
        user1_profile = models.UserProfile.objects.create(
            user=user1,
            name="John McDowell",
            picture="https://example.com/default_profile_picture.jpg",
        )

        user2 = User.objects.create_user(
            username="testdiplomacy51",
            email="testdiplomacy51@gmail.com",
        )
        user2_profile = models.UserProfile.objects.create(
            user=user2,
            name="Test Diplomacy",
            picture="https://example.com/default_profile_picture.jpg",
        )

        # Create Pending Games
        pending_game_1 = models.Game.objects.create(
            variant=classical_variant, status=models.Game.PENDING
        )
        models.Member.objects.create(game=pending_game_1, user=user1)
        phase_1 = models.Phase.objects.create(
            game=pending_game_1,
            status=models.Phase.PENDING,
            season="Spring",
            year=1901,
            type="Movement",
        )
        self._create_units_and_supply_centers(phase_1, classical_variant)

        pending_game_2 = models.Game.objects.create(
            variant=italy_vs_germany_variant, status=models.Game.PENDING
        )
        models.Member.objects.create(game=pending_game_2, user=user1)
        phase_2 = models.Phase.objects.create(
            game=pending_game_2,
            status=models.Phase.PENDING,
            season="Spring",
            year=1901,
            type="Movement",
        )
        self._create_units_and_supply_centers(phase_2, italy_vs_germany_variant)

        # Create Active Game
        active_game_1 = models.Game.objects.create(
            variant=italy_vs_germany_variant, status=models.Game.ACTIVE
        )
        member1 = models.Member.objects.create(game=active_game_1, user=user1)
        member2 = models.Member.objects.create(game=active_game_1, user=user2)

        # Assign Nations
        nations = active_game_1.variant.nations
        member1.nation = nations[0].get("name")
        member1.save()
        member2.nation = nations[1].get("name")
        member2.save()

        # Create Current Phase
        current_phase = models.Phase.objects.create(
            game=active_game_1,
            status=models.Phase.ACTIVE,
            season="Spring",
            year=1901,
            type="Movement",
        )
        self._create_units_and_supply_centers(current_phase, italy_vs_germany_variant)

        # Create Orders
        germany_phase_state = models.PhaseState.objects.create(
            member=models.Member.objects.get(nation="Germany", game=active_game_1),
            phase=current_phase,
        )
        italy_phase_state = models.PhaseState.objects.create(
            member=models.Member.objects.get(nation="Italy", game=active_game_1),
            phase=current_phase,
        )

        models.Order.objects.create(
            phase_state=italy_phase_state,
            order_type="Move",
            source="rom",
            target="ven",
        )

        models.Order.objects.create(
            phase_state=germany_phase_state,
            order_type="Move",
            source="ber",
            target="mun",
        )

        self.stdout.write("Test data generation complete.")

    def _create_units_and_supply_centers(self, phase, variant):
        """Helper method to create units and supply centers for a phase."""
        for unit_data in variant.start["units"]:
            models.Unit.objects.create(
                phase=phase,
                type=unit_data["type"].lower(),
                nation=unit_data["nation"],
                province=unit_data["province"],
            )

        for sc_data in variant.start["supply_centers"]:
            models.SupplyCenter.objects.create(
                phase=phase,
                nation=sc_data["nation"],
                province=sc_data["province"],
            )
