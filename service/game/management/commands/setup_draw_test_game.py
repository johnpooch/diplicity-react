from django.core.management.base import BaseCommand, CommandError

from common.constants import GameStatus
from game.models import Game
from supply_center.models import SupplyCenter


class Command(BaseCommand):
    help = "Sets up an Italy vs Germany game for draw proposal testing by redistributing supply centers"

    def add_arguments(self, parser):
        parser.add_argument("game_id", type=str, help="The ID of the game to modify")

    def handle(self, *args, **options):
        game_id = options["game_id"]

        try:
            game = Game.objects.select_related("variant").get(id=game_id)
        except Game.DoesNotExist:
            raise CommandError(f"Game with ID '{game_id}' does not exist")

        if game.variant.id != "italy-vs-germany":
            raise CommandError(
                f"Game must use 'italy-vs-germany' variant. "
                f"This game uses '{game.variant.id}'"
            )

        if game.status != GameStatus.ACTIVE:
            raise CommandError(f"Game must be active. Current status: {game.status}")

        variant = game.variant
        italy = variant.nations.get(name="Italy")
        germany = variant.nations.get(name="Germany")
        phase = game.current_phase

        if not phase:
            raise CommandError("Game has no current phase")

        owned_province_ids = phase.supply_centers.values_list("province_id", flat=True)
        neutral_sc_provinces = variant.provinces.filter(supply_center=True).exclude(
            id__in=owned_province_ids
        )

        supply_centers_to_create = []
        for i, province in enumerate(neutral_sc_provinces):
            nation = italy if i % 2 == 0 else germany
            supply_centers_to_create.append(
                SupplyCenter(phase=phase, nation=nation, province=province)
            )
        SupplyCenter.objects.bulk_create(supply_centers_to_create)

        italy_scs = phase.supply_centers.filter(nation=italy).count()
        germany_scs = phase.supply_centers.filter(nation=germany).count()
        total_scs = italy_scs + germany_scs
        threshold = variant.solo_victory_sc_count

        self.stdout.write(self.style.SUCCESS(f"\nGame updated: {game.name}"))
        self.stdout.write(f"URL: http://localhost:5173/game/{game.id}")
        self.stdout.write(f"\nSupply centers:")
        self.stdout.write(f"  Italy: {italy_scs}")
        self.stdout.write(f"  Germany: {germany_scs}")
        self.stdout.write(f"  Total: {total_scs}")
        self.stdout.write(f"  Victory threshold: {threshold}")

        if total_scs >= threshold:
            self.stdout.write(self.style.SUCCESS("\nGame is now draw-ready!"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\nWarning: Total SCs ({total_scs}) still below threshold ({threshold})"
                )
            )
