import requests

from .serializers import AdjudicationSerializer
from common.constants import ADJUDICATION_BASE_URL


def _make_adjudication_request(phase, endpoint, method="GET", data=None):
    url = f"{ADJUDICATION_BASE_URL}/{endpoint}/{phase.variant.name}"
    context = {"game": phase.game}

    if method.upper() == "POST":
        response = requests.post(url, json=data)
    else:
        response = requests.get(url)

    response.raise_for_status()
    response_data = response.json()
    serializer = AdjudicationSerializer(data=response_data, context=context)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def start(phase):
    return _make_adjudication_request(phase, "start-with-options")


def resolve(phase):
    serialized_phase = AdjudicationSerializer(phase, context={"game": phase.game}).data
    return _make_adjudication_request(phase, "resolve-with-options", method="POST", data=serialized_phase)
