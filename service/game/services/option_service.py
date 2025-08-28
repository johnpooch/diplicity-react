import logging
from django.shortcuts import get_object_or_404
from rest_framework import exceptions

from .. import models
from .base_service import BaseService

logger = logging.getLogger("game")


class OptionService(BaseService):
    def __init__(self, user):
        self.user = user

    def list(self, game_id, phase_id):
        """
        List the provinces that the player can order for in the current phase.
        Returns a list of options with province and optional unit information.
        """
        logger.info(f"OptionService.list() called with game_id: {game_id}, phase_id: {phase_id}")

        # Get the game and verify the user is a member
        game = get_object_or_404(models.Game, id=game_id)
        member = game.members.filter(user=self.user).first()
        
        if not member:
            raise exceptions.PermissionDenied(detail="You are not a member of this game.")

        # Get the phase
        phase = get_object_or_404(models.Phase, id=phase_id, game=game)
        
        # Get the nation for the current user
        nation = member.nation
        
        # Get the options for this nation in this phase
        options = phase.options_dict.get(nation, {})
        
        # Build the result list
        result = []
        for province_id in options.keys():
            # Get province data from variant
            province_data = next((p for p in game.variant.provinces if p["id"] == province_id), None)
            if not province_data:
                continue
                
            # Check if there's a unit in this province
            unit = phase.units.filter(province=province_id).first()
            
            # Create province serializer data
            province_serializer_data = {
                "id": province_data["id"],
                "name": province_data["name"],
                "type": province_data["type"],
                "supply_center": province_data.get("supply_center", False)
            }
            
            # Create unit serializer data if unit exists
            unit_serializer_data = None
            if unit:
                unit_serializer_data = {
                    "type": unit.type,
                    "nation": {"name": unit.nation},
                    "province": province_serializer_data
                }
            
            result.append({
                "province": province_serializer_data,
                "unit": unit_serializer_data
            })
        
        return result
