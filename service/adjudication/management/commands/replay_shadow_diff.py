from django.core.management.base import BaseCommand, CommandError

from adjudication.models import ShadowAdjudicationDiff
from adjudication.service import compute_shadow_diff
from variant.utils import variant_to_canonical_dict


class Command(BaseCommand):
    help = (
        "Re-run the Python adjudicator for a stored ShadowAdjudicationDiff "
        "and re-diff it against the recorded godip response."
    )

    def add_arguments(self, parser):
        parser.add_argument("diff_id", type=int)

    def handle(self, *args, **options):
        diff_id = options["diff_id"]
        try:
            record = ShadowAdjudicationDiff.objects.select_related(
                "phase", "phase__variant"
            ).get(pk=diff_id)
        except ShadowAdjudicationDiff.DoesNotExist:
            raise CommandError(f"ShadowAdjudicationDiff {diff_id} does not exist")

        canonical_variant = variant_to_canonical_dict(record.phase.variant)
        diff, _ = compute_shadow_diff(
            canonical_variant, record.pre_state, record.godip_response
        )

        self.stdout.write(
            f"ShadowAdjudicationDiff {record.id} — phase {record.phase_id} "
            f"({record.phase.name})"
        )
        self.stdout.write(f"  recorded tier: {record.tier}")

        if diff.matched:
            self.stdout.write(
                self.style.SUCCESS("  replay: no diff — the mismatch no longer reproduces")
            )
            return

        self.stdout.write(self.style.WARNING(f"  replay tier: {diff.tier}"))
        for field_diff in diff.field_diffs:
            self.stdout.write(f"    [{field_diff.tier}] {field_diff.field}")
            for item in field_diff.only_in_godip:
                self.stdout.write(f"      godip only:  {item}")
            for item in field_diff.only_in_python:
                self.stdout.write(f"      python only: {item}")
