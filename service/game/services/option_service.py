import logging
from django.shortcuts import get_object_or_404
from rest_framework import exceptions

from .. import models
from .base_service import BaseService

logger = logging.getLogger("game")


class OptionService(BaseService):
    def __init__(self, user):
        self.user = user

    def _build_option_results(self, game, phase, options_keys):
        """
        Helper method to build option results from a list of option keys.
        """
        result = []
        for key in options_keys:
            if key == 'Type':
                continue
                
            # Get province data from variant
            province_data = next((p for p in game.variant.provinces if p["id"] == key), None)
            if not province_data:
                continue
                
            # Check if there's a unit in this province
            unit = phase.units.filter(province=key).first()
            
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
                    "province": province_serializer_data,
                    "dislodged": unit.dislodged
                }
            
            result.append({
                "province": province_serializer_data,
                "unit": unit_serializer_data
            })
        
        return result

    def list(self, game_id, phase_id):
        """
        Get initial options for order building (top-level provinces).
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
        
        # Return initial options (top-level provinces)
        return self._build_option_results(game, phase, options.keys())

    def get_options_for_order(self, game_id, phase_id, partial_order):
        """
        Get available options for order building based on a partial order.
        Returns the next available options for the given partial order.
        """
        logger.info(f"OptionService.get_options_for_order() called with game_id: {game_id}, phase_id: {phase_id}, order: {partial_order}")

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
        print(f"Options: {options}")
        
        # If no partial order, return initial options (same as list method)
        if not partial_order:
            return self.list(game_id, phase_id)
        
        # Traverse the options tree based on the partial order
        current_options = options
        
        # Handle the partial order traversal
        # The partial order should contain the actual values, not field names
        if 'source' in partial_order and partial_order['source']:
            source_province = partial_order['source']
            if source_province in current_options:
                current_options = current_options[source_province].get('Next', {})
            else:
                raise exceptions.ValidationError(f"Invalid source province: {source_province}")

        if 'order_type' in partial_order and partial_order['order_type']:
            order_type = partial_order['order_type']
            if order_type in current_options:
                current_options = current_options[order_type].get('Next', {})
            else:
                raise exceptions.ValidationError(f"Invalid order type: {order_type}")
        
        if 'target' in partial_order and partial_order['target']:
            target_province = partial_order['target']
            if target_province in current_options:
                current_options = current_options[target_province].get('Next', {})
            else:
                raise exceptions.ValidationError(f"Invalid target province: {target_province}")
        
        if 'aux' in partial_order and partial_order['aux']:
            aux_province = partial_order['aux']
            if aux_province in current_options:
                current_options = current_options[aux_province].get('Next', {})
            else:
                raise exceptions.ValidationError(f"Invalid aux province: {aux_province}")
        
        # Extract the available options from the current level
        return self._build_option_results(game, phase, current_options.keys())
