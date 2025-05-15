import json
import requests

from ..serializers import AdjudicationResponseSerializer, AdjudicationGameSerializer
from .base_service import BaseService


class AdjudicationService(BaseService):

    base_url = "https://godip-adjudication.appspot.com"

    def __init__(self, user):
        self.user = user

    def start(self, game):
        response = requests.get(
            f"{self.base_url}/start-with-options/{game.variant.name}",
        )

        response.raise_for_status()

        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)

        serializer = AdjudicationResponseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def resolve(self, game):

        request_data = AdjudicationGameSerializer(game)

        response = requests.post(
            f"{self.base_url}/resolve-with-options/{game.variant.name}",
            json=request_data.data,
            headers={
                "Content-Type": "application/json",
            },
        )

        response.raise_for_status()

        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)

        serializer = AdjudicationResponseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
