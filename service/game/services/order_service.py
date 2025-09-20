from django.shortcuts import get_object_or_404
from rest_framework import exceptions

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

        order = models.Order.objects.create(
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

    def list(self, game_id, phase_id):
        game = get_object_or_404(models.Game, id=game_id)
        phase = game.phases.filter(id=phase_id).first()
        if not phase:
            raise exceptions.NotFound("Phase not found.")

        if phase.status == phase.COMPLETED:
            phase_states = phase.phase_states.all()
        else:
            phase_states = phase.phase_states.filter(member__user=self.user)

        orders = []
        for phase_state in phase_states:
            orders.extend(phase_state.orders.select_related('resolution').all())

        grouped_orders = {}
        for order in orders:
            nation = order.phase_state.member.nation
            if nation not in grouped_orders:
                grouped_orders[nation] = []
            grouped_orders[nation].append(order)

        # Enhance orders with province data for target and aux
        province_lookup = {
            p["id"]: p for p in game.variant.provinces
        }
        
        enhanced_grouped_orders = {}
        for nation, nation_orders in grouped_orders.items():
            enhanced_orders = []
            for order in nation_orders:
                # Safely get resolution (might not exist)
                resolution = None
                try:
                    resolution = order.resolution
                except:
                    resolution = None
                    
                enhanced_order = {
                    "id": order.id,
                    "order_type": order.order_type,
                    "unit_type": order.unit_type,
                    "source": province_lookup.get(order.source),
                    "target": province_lookup.get(order.target) if order.target else None,
                    "aux": province_lookup.get(order.aux) if order.aux else None,
                    "resolution": resolution
                }
                enhanced_orders.append(enhanced_order)
            enhanced_grouped_orders[nation] = enhanced_orders

        return enhanced_grouped_orders

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

    def create_interactive(self, game_id, selected_array):
        """
        Interactive order creation - returns next available options based on current selection.
        
        Args:
            game_id: The game ID
            selected_array: List of strings representing the current selection path
        
        Returns:
            Dict with options, step, title, completed, can_go_back
        """
        game = get_object_or_404(models.Game, id=game_id)
        member = game.members.filter(user=self.user).first()

        province_lookup = {
            p["id"]: p for p in game.variant.provinces
        }
        
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
                detail="Cannot create orders for eliminated players."
            )

        # Use OptionsService to get next options
        from .options_service import OptionsService
        options_service = OptionsService(current_phase.options_dict, game.variant)
        
        try:
            result = options_service.list_options_for_selected(member.nation, selected_array)
            result["selected"] = selected_array
            
            # If the order is complete, create the actual order
            if result["completed"]:
                # Convert the selected path to order data
                order_data = options_service.convert_to_order_data(member.nation, selected_array)
                
                # Create the order using the existing create method
                created_order = self.create(game_id, order_data)

                # Safely get resolution (might not exist)
                resolution = None
                try:
                    resolution = created_order.resolution
                except:
                    resolution = None

                enhanced_order = {
                    "id": created_order.id,
                    "order_type": created_order.order_type,
                    "source": province_lookup.get(created_order.source),
                    "target": province_lookup.get(created_order.target) if created_order.target else None,
                    "aux": province_lookup.get(created_order.aux) if created_order.aux else None,
                    "resolution": resolution
                }
                
                # Add the created order to the result
                result["created_order"] = enhanced_order
            
            return result
        except Exception as e:
            raise exceptions.ValidationError(
                detail=f"Error getting order options: {str(e)}"
            )
