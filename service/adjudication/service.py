import json
import logging
import requests

from .serializers import AdjudicationSerializer
from common.constants import ADJUDICATION_BASE_URL

logger = logging.getLogger(__name__)


def _make_adjudication_request(phase, endpoint, method="GET", data=None):
    url = f"{ADJUDICATION_BASE_URL}/{endpoint}/{phase.variant.name}"
    context = {"game": phase.game}

    # Log the request attempt
    logger.info(f"Making {method.upper()} request to adjudication service: {url}")
    if data and method.upper() == "POST":
        logger.info(f"Request payload: {json.dumps(data, indent=2)}")

    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)

        logger.info(f"Received response with status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Response data: {json.dumps(response_data, indent=2)}")

        serializer = AdjudicationSerializer(data=response_data, context=context)
        serializer.is_valid(raise_exception=True)

        logger.info(f"Successfully processed adjudication request for endpoint: {endpoint}")
        return serializer.validated_data

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred for {method.upper()} {url}: {e}")
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response text: {response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception occurred for {method.upper()} {url}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from {url}: {e}")
        logger.error(f"Response text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during adjudication request to {url}: {e}")
        if "response" in locals():
            logger.error(f"Response status: {response.status_code}, text: {response.text}")
        raise


def start(phase):
    logger.info(f"Starting adjudication for phase {phase.id} of game {phase.game.id}")
    return _make_adjudication_request(phase, "start-with-options")


def resolve(phase):
    logger.info(f"Resolving adjudication for phase {phase.id} of game {phase.game.id}")
    serialized_phase = AdjudicationSerializer(phase, context={"game": phase.game}).data
    return _make_adjudication_request(phase, "resolve-with-options", method="POST", data=serialized_phase)
