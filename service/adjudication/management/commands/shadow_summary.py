from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.utils.dateparse import parse_date

from adjudication.models import ShadowAdjudicationDiff


class Command(BaseCommand):
    help = (
        "Summarise shadow-mode adjudication mismatches recorded in "
        "ShadowAdjudicationDiff — the view that gates the adjudicator cutover."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            type=str,
            default=None,
            help="Only count diffs recorded on or after this date (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--top",
            type=int,
            default=10,
            help="Number of most-affected phases to list (default 10).",
        )
        parser.add_argument(
            "--total-resolutions",
            type=int,
            default=None,
            help=(
                "Total shadow-mode resolutions run, read from the "
                "adjudication.shadow.* telemetry counters. Enables match-rate "
                "reporting, which the database alone cannot provide since only "
                "mismatches are persisted."
            ),
        )

    def handle(self, *args, **options):
        queryset = ShadowAdjudicationDiff.objects.all()

        window = "all time"
        if options["since"]:
            since = parse_date(options["since"])
            if since is None:
                raise CommandError(f"Could not parse --since date: {options['since']!r}")
            queryset = queryset.filter(created_at__date__gte=since)
            window = f"since {since}"

        total_mismatches = queryset.count()

        self.stdout.write(f"Shadow adjudication summary ({window})")
        self.stdout.write(f"  mismatches recorded: {total_mismatches}")

        total_resolutions = options["total_resolutions"]
        if total_resolutions is not None:
            matches = total_resolutions - total_mismatches
            rate = (matches / total_resolutions * 100) if total_resolutions else 0.0
            self.stdout.write(f"  resolutions run:     {total_resolutions}")
            self.stdout.write(f"  match rate:          {rate:.2f}%")
        else:
            self.stdout.write(
                "  match rate:          unavailable — pass --total-resolutions "
                "(matches are telemetry-only, not stored)"
            )

        tier_counts = {
            row["tier"]: row["count"]
            for row in queryset.values("tier").annotate(count=Count("id"))
        }
        self.stdout.write("  mismatches by tier:")
        for tier, _label in ShadowAdjudicationDiff.TIER_CHOICES:
            self.stdout.write(f"    {tier}: {tier_counts.get(tier, 0)}")

        top = options["top"]
        top_phases = (
            queryset.values(
                "phase_id",
                "phase__season",
                "phase__year",
                "phase__type",
                "phase__game__name",
            )
            .annotate(count=Count("id"))
            .order_by("-count")[:top]
        )
        self.stdout.write(f"  top {top} phases by mismatch count:")
        if not top_phases:
            self.stdout.write("    (none)")
        for row in top_phases:
            label = f"{row['phase__season']} {row['phase__year']}, {row['phase__type']}"
            game = row["phase__game__name"] or "-"
            self.stdout.write(
                f"    phase {row['phase_id']} ({label}, game: {game}): {row['count']}"
            )
