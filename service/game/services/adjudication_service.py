import json
import requests

from ..serializers import AdjudicationResponseSerializer, AdjudicationGameSerializer
from .base_service import BaseService


class AdjudicationService(BaseService):

    base_url = "https://godip-adjudication.appspot.com"

    def __init__(self, user):
        self.user = user

    def _filter_options_by_variant_nations(self, data, game):
        """
        Filter the options object to only include nations that belong to the variant.
        """
        if 'options' not in data:
            return data
        
        # Get valid nation names from the variant
        valid_nations = {nation['name'] for nation in game.variant.nations}
        
        # Filter the options to only include valid nations
        filtered_options = {
            nation: options 
            for nation, options in data['options'].items() 
            if nation in valid_nations
        }
        
        data['options'] = filtered_options
        return data

    def start(self, game):
        response = requests.get(
            f"{self.base_url}/start-with-options/{game.variant.name}",
        )

        response.raise_for_status()

        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)

        # Filter options to only include variant nations
        data = self._filter_options_by_variant_nations(data, game)

        serializer = AdjudicationResponseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def resolve(self, game):

        request_data = AdjudicationGameSerializer(game)

        print(request_data.data)

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

        # Filter options to only include variant nations
        data = self._filter_options_by_variant_nations(data, game)

        serializer = AdjudicationResponseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
