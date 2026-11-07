import os

import requests
from django.core.management.base import BaseCommand

MARKER_URL = "https://api.honeycomb.io/1/markers/__all__"


class Command(BaseCommand):
    help = "Posts a Honeycomb marker for the backend release being deployed"

    def handle(self, *args, **options):
        sha = os.getenv("RAILWAY_GIT_COMMIT_SHA")
        api_key = os.getenv("HONEYCOMB_MARKERS_API_KEY")
        if (
            not sha
            or not api_key
            or os.getenv("RAILWAY_ENVIRONMENT_NAME") != "production"
        ):
            return

        try:
            response = requests.post(
                MARKER_URL,
                headers={"X-Honeycomb-Team": api_key},
                json={"type": "backend-deploy", "message": f"Backend deploy {sha}"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException:
            self.stderr.write("Failed to create Honeycomb marker.")
