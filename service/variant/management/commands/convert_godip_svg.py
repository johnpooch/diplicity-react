from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from variant.utils import convert_godip_dsvg


class Command(BaseCommand):
    help = "Convert a godip variant SVG into a dSVG."

    def add_arguments(self, parser):
        parser.add_argument("input", type=str)
        parser.add_argument("--output", type=str, required=False)

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        if not input_path.is_file():
            raise CommandError(f"Input file not found: {input_path}")

        dsvg, warnings = convert_godip_dsvg(input_path.read_text())

        for warning in warnings:
            self.stderr.write(self.style.WARNING(warning))

        output = options.get("output")
        if output:
            Path(output).write_text(dsvg)
            self.stdout.write(self.style.SUCCESS(f"Wrote {output}"))
        else:
            self.stdout.write(dsvg)
