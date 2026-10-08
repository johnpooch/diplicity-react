from datetime import UTC, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from harvest.build import Harvest
from harvest.exceptions import HarvestError
from harvest.snapshot import read_snapshot
from select_orders.evals import FIXTURES_DIR
from select_orders.fixtures import write_fixture


class Command(BaseCommand):
    help = "Build schema v2 select_orders fixtures from a snapshot written by harvest/export.sql."

    def add_arguments(self, parser):
        parser.add_argument("snapshot", help="path to the snapshot JSON")
        parser.add_argument("--phase", type=int, action="append", help="phase id to harvest; repeatable")
        parser.add_argument("--nation", action="append", help="eval nation to harvest; repeatable")
        parser.add_argument("--out", default=str(FIXTURES_DIR), help="directory to write fixtures into")

    def handle(self, *args, **options):
        try:
            snapshot = read_snapshot(Path(options["snapshot"]))
        except HarvestError as e:
            raise CommandError(str(e)) from e
        harvest = Harvest(snapshot, harvested_at=datetime.now(UTC).isoformat(timespec="seconds"))
        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        written = 0
        for phase_id in options["phase"] or harvest.phase_ids():
            try:
                fixtures = harvest.fixtures(phase_id, options["nation"])
            except HarvestError as e:
                self.stderr.write(f"skip phase {phase_id}: {e}")
                continue
            for fixture in fixtures:
                path = out / f"{fixture['id']}.json"
                if path.exists():
                    self.stdout.write(f"exists, left as is: {path}")
                    continue
                write_fixture(path, fixture)
                written += 1
                self.stdout.write(f"wrote {path}")
        self.stdout.write(f"{written} fixture(s) written")
