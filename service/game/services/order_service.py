from django.shortcuts import get_object_or_404
from rest_framework import exceptions

from django.apps import apps
from .. import models
from .base_service import BaseService


class OrderService(BaseService):
    def __init__(self, user):
        self.user = user

    def create(self, game_id, data):
        game = get_object_or_404(models.Game, id=game_id)

        member = game.members.filter(user=self.user).first()
        if not member:
            raise exceptions.PermissionDenied(
                detail="User is not a member of the game."
            )

        if member.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for eliminated players."
            )

        if member.kicked:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for kicked players."
            )

        if game.status != models.Game.ACTIVE:
            raise exceptions.ValidationError(
                detail="Orders can only be created for active games."
            )

        current_phase = game.current_phase
        if current_phase is None:
            raise exceptions.ValidationError(
                detail="No current phase found for the game."
            )

        current_phase_state = current_phase.phase_states.filter(
            member__user=self.user
        ).first()
        if current_phase_state.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot create orders for eliminated players."
            )

        # Check for existing order with same source
        existing_order = current_phase_state.orders.filter(source=data["source"]).first()

        if existing_order:
            # Update existing order
            existing_order.order_type = data["order_type"]
            existing_order.target = data.get("target")
            existing_order.aux = data.get("aux")
            existing_order.unit_type = data.get("unit_type")
            try:
                existing_order.full_clean()
            except Exception as e:
                raise exceptions.ValidationError(e)
            existing_order.save()
            return existing_order

        Order = apps.get_model('order', 'Order')
        order = Order.objects.create(
            phase_state=current_phase_state,
            order_type=data["order_type"],
            source=data["source"],
            target=data.get("target"),
            aux=data.get("aux"),
            unit_type=data.get("unit_type"),
        )

        try:
            order.full_clean()
        except Exception as e:
            raise exceptions.ValidationError(e)

        order.save()
        return order


    def list_orderable_provinces(self, game_id):
        """
        Lists the provinces that the user can order for the current phase,
        along with any existing orders for those provinces.
        """
        game = get_object_or_404(models.Game, id=game_id)
        member = game.members.filter(user=self.user).first()
        
        if not member:
            raise exceptions.PermissionDenied(
                detail="User is not a member of the game."
            )

        if member.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot list orders for eliminated players."
            )

        if member.kicked:
            raise exceptions.PermissionDenied(
                detail="Cannot list orders for kicked players."
            )

        # Get the current phase
        current_phase = game.current_phase
        if not current_phase:
            raise exceptions.ValidationError(
                detail="No current phase found for the game."
            )

        # Get the user's current phase state
        current_phase_state = current_phase.phase_states.filter(
            member__user=self.user
        ).first()
        
        if not current_phase_state:
            raise exceptions.ValidationError(
                detail="No phase state found for user."
            )

        if current_phase_state.eliminated:
            raise exceptions.PermissionDenied(
                detail="Cannot list orders for eliminated players."
            )

        # Use OptionsService to get orderable provinces
        from .options_service import OptionsService
        options_service = OptionsService(current_phase.options_dict, game.variant)
        
        try:
            orderable_provinces = options_service.list_options_for_nation(member.nation)
        except Exception as e:
            raise exceptions.ValidationError(
                detail=f"Error getting orderable provinces: {str(e)}"
            )

        # Create a lookup dict for province data
        province_lookup = {
            p["id"]: p for p in game.variant.provinces
        }

        # Build result data
        result = []
        for province_id in orderable_provinces:
            # Get province data from variant
            province_data = province_lookup.get(province_id)
            
            if not province_data:
                continue
            
            # Check for existing order
            existing_order = current_phase_state.orders.filter(source=province_id).first()
            
            # Enhance order with province data for target and aux
            order_data = existing_order
            if existing_order:
                # Safely get resolution (might not exist)
                resolution = None
                try:
                    resolution = existing_order.resolution
                except:
                    resolution = None
                    
                order_data = {
                    "id": existing_order.id,
                    "order_type": existing_order.order_type,
                    "source": province_lookup.get(existing_order.source),
                    "target": province_lookup.get(existing_order.target) if existing_order.target else None,
                    "aux": province_lookup.get(existing_order.aux) if existing_order.aux else None,
                    "resolution": resolution
                }
            
            result.append({
                "province": province_data,
                "order": order_data
            })

        return result

