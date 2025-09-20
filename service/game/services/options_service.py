class InvalidOrderStateException(Exception):
    """Exception raised when invalid order state is encountered during options traversal."""
    pass


class OptionsService:
    """
    Service for traversing the options tree for dynamic order creation.
    Based on the approach outlined in documentation/dynamic_order_creation.md
    """
    
    def __init__(self, options_dict, variant):
        """
        Initialize with the options dictionary from a Phase and variant data.
        
        Args:
            options_dict: The parsed JSON options from Phase.options_dict
            variant: The Variant model instance for getting province names
        """
        self.options = options_dict
        self.variant = variant
        
        # Create a lookup dict for province data
        self.province_lookup = {
            province["id"]: province for province in variant.provinces
        }

    def _get_province_display_name(self, province_id):
        """Get the proper display name for a province."""
        province_data = self.province_lookup.get(province_id)
        if province_data:
            return province_data.get("name", province_id.title())
        return province_id.title()

    def list_options_for_nation(self, nation):
        """
        Lists the orderable provinces for the given nation.
        
        Args:
            nation: The nation name (e.g., "England")
            
        Returns:
            List of province names that can be ordered for this nation
            
        Raises:
            InvalidOrderStateException: If nation is not found in options
        """
        if nation not in self.options:
            raise InvalidOrderStateException(f"Nation '{nation}' not found in options")
        
        return list(self.options[nation].keys())

    def list_options_for_selected(self, nation, selected):
        """
        Lists the options based on the partially completed order.
        
        Args:
            nation: The nation name
            selected: List of strings representing the partial order path
                     e.g., ["bud"] for just province selected
                     e.g., ["bud", "Move"] for province and order type selected
                     
        Returns:
            Dict with structure:
            {
                "options": [list of available options],
                "step": str,  # current step identifier
                "title": str,  # human readable description
                "completed": bool,  # whether order is complete
                "can_go_back": bool  # whether user can go back a step
            }
            
        Raises:
            InvalidOrderStateException: If nation or selected path is invalid
        """
        if nation not in self.options:
            raise InvalidOrderStateException(f"Nation '{nation}' not found in options")
        
        if not selected:
            raise InvalidOrderStateException("Selected options cannot be empty - province must be selected first")
        
        nation_options = self.options[nation]
        
        if len(selected) == 1:
            # Province selected - show available order types
            province = selected[0]
            if province not in nation_options:
                raise InvalidOrderStateException(f"Province '{province}' not available for nation '{nation}'")
            
            order_types = list(nation_options[province]["Next"].keys())
            return {
                "options": [{"value": ot, "label": ot} for ot in order_types],
                "step": "select-order-type",
                "title": f"Select order type for {self._get_province_display_name(province)}",
                "completed": False,
                "can_go_back": False
            }
        
        if len(selected) == 2:
            # Province and order type selected
            province, order_type = selected
            
            if province not in nation_options:
                raise InvalidOrderStateException(f"Province '{province}' not available for nation '{nation}'")
            
            if order_type not in nation_options[province]["Next"]:
                raise InvalidOrderStateException(f"Order type '{order_type}' not available for province '{province}'")
            
            order_config = nation_options[province]["Next"][order_type]

            if order_type == "Build":
                unit_types = list(order_config["Next"].keys())
                # Build orders need a unit type
                return {
                    "options": [{"value": unit_type, "label": unit_type} for unit_type in unit_types],
                    "step": "select-unit-type",
                    "title": f"Select unit type to build in {self._get_province_display_name(province)}",
                    "completed": False,
                    "can_go_back": True
                }
            
            if order_type == "Hold":
                # Hold orders are complete with just province + order type
                return {
                    "options": [],
                    "step": "completed",
                    "title": f"{self._get_province_display_name(province)} will hold",
                    "completed": True,
                    "can_go_back": False
                }
            
            if order_type == "Move":
                # Move orders need a target
                if (province in order_config["Next"] and 
                    "Next" in order_config["Next"][province]):
                    targets = list(order_config["Next"][province]["Next"].keys())
                    return {
                        "options": [{"value": target, "label": self._get_province_display_name(target)} for target in targets],
                        "step": "select-destination",
                        "title": f"Select province to move {self._get_province_display_name(province)} to",
                        "completed": False,
                        "can_go_back": True
                    }
                else:
                    raise InvalidOrderStateException(f"No valid move targets found for province '{province}'")
            
            if order_type in ["Support", "Convoy"]:
                # Support/Convoy orders need auxiliary province selection first
                if (province in order_config["Next"] and 
                    "Next" in order_config["Next"][province]):
                    aux_options = list(order_config["Next"][province]["Next"].keys())
                    return {
                        "options": [{"value": aux, "label": self._get_province_display_name(aux)} for aux in aux_options],
                        "step": "select-auxiliary",
                        "title": f"Select province to {order_type.lower()} for {self._get_province_display_name(province)}",
                        "completed": False,
                        "can_go_back": True
                    }
                else:
                    raise InvalidOrderStateException(f"No valid auxiliary provinces found for {order_type} from '{province}'")
        
        if len(selected) == 3:
            province, order_type, param = selected
            
            # Validate province and order type first
            if province not in nation_options:
                raise InvalidOrderStateException(f"Province '{province}' not available for nation '{nation}'")
            
            if order_type not in nation_options[province]["Next"]:
                raise InvalidOrderStateException(f"Order type '{order_type}' not available for province '{province}'")
            
            if order_type == "Move":
                # Validate move target
                order_config = nation_options[province]["Next"][order_type]
                if (province not in order_config["Next"] or 
                    "Next" not in order_config["Next"][province] or
                    param not in order_config["Next"][province]["Next"]):
                    raise InvalidOrderStateException(f"Invalid move target '{param}' for province '{province}'")
                
                # Move order is complete
                return {
                    "options": [],
                    "step": "completed", 
                    "title": f"{self._get_province_display_name(province)} will move to {self._get_province_display_name(param)}",
                    "completed": True,
                    "can_go_back": False
                }

            if order_type == "Build":
                # Build order is complete
                return {
                    "options": [],
                    "step": "completed",
                    "title": f"{param} will be built in {self._get_province_display_name(province)}",
                    "completed": True,
                    "can_go_back": False
                }
            
            if order_type in ["Support", "Convoy"]:
                # Support/Convoy with aux selected, now need target
                order_config = nation_options[province]["Next"][order_type]
                if (province not in order_config["Next"] or
                    "Next" not in order_config["Next"][province] or
                    param not in order_config["Next"][province]["Next"]):
                    raise InvalidOrderStateException(f"Invalid auxiliary province '{param}' for {order_type} from '{province}'")
                
                if "Next" in order_config["Next"][province]["Next"][param]:
                    targets = list(order_config["Next"][province]["Next"][param]["Next"].keys())
                    return {
                        "options": [{"value": target, "label": self._get_province_display_name(target)} for target in targets],
                        "step": "select-target",
                        "title": f"Select target for {order_type.lower()} order",
                        "completed": False,
                        "can_go_back": True
                    }
                else:
                    raise InvalidOrderStateException(f"No valid targets found for {order_type} from '{province}' with auxiliary '{param}'")
        
        if len(selected) == 4:
            province, order_type, aux, target = selected
            
            # Validate the complete path
            if province not in nation_options:
                raise InvalidOrderStateException(f"Province '{province}' not available for nation '{nation}'")
            
            if order_type not in nation_options[province]["Next"]:
                raise InvalidOrderStateException(f"Order type '{order_type}' not available for province '{province}'")
            
            if order_type in ["Support", "Convoy"]:
                order_config = nation_options[province]["Next"][order_type]
                if (province not in order_config["Next"] or
                    aux not in order_config["Next"][province]["Next"] or
                    target not in order_config["Next"][province]["Next"][aux]["Next"]):
                    raise InvalidOrderStateException(f"Invalid {order_type.lower()} order: '{province}' -> '{aux}' -> '{target}'")
                
                return {
                    "options": [],
                    "step": "completed",
                    "title": f"{self._get_province_display_name(province)} will {order_type.lower()} {self._get_province_display_name(aux)} to {self._get_province_display_name(target)}",
                    "completed": True,
                    "can_go_back": False
                }
            else:
                raise InvalidOrderStateException(f"Invalid order state: 4 selections for order type '{order_type}'")
        
        # Invalid selection length
        raise InvalidOrderStateException(f"Invalid selection length: {len(selected)} items")

    def validate_complete_order(self, nation, selected):
        """
        Validates that a complete order is valid according to the options tree.
        
        Args:
            nation: The nation name
            selected: List representing complete order path
            
        Returns:
            bool: True if the order is valid and complete
        """
        try:
            result = self.list_options_for_selected(nation, selected)
            return result["completed"]
        except InvalidOrderStateException:
            return False

    def convert_to_order_data(self, nation, selected):
        """
        Converts a completed selected path to order data format.
        
        Args:
            nation: The nation name
            selected: Complete selected path
            
        Returns:
            Dict with order_type, source, target, aux fields
            
        Raises:
            InvalidOrderStateException: If the order is invalid or incomplete
        """
        if not self.validate_complete_order(nation, selected):
            raise InvalidOrderStateException(f"Invalid or incomplete order: {selected}")
        
        if len(selected) == 2 and selected[1] == "Hold":
            # Hold order: [province, "Hold"]
            return {
                "order_type": "Hold",
                "source": selected[0],
                "target": None,
                "aux": None
            }
        
        if len(selected) == 3 and selected[1] == "Move":
            # Move order: [province, "Move", target]
            return {
                "order_type": "Move", 
                "source": selected[0],
                "target": selected[2],
                "aux": None
            }

        if len(selected) == 3 and selected[1] == "Build":
            # Build order: [province, "Build", unit_type]
            print("Build order")
            print(f"Selected: {selected}")
            return {
                "order_type": "Build",
                "source": selected[0],
                "target": None,
                "unit_type": selected[2],
                "aux": None
            }
        
        if len(selected) == 4 and selected[1] in ["Support", "Convoy"]:
            # Support/Convoy order: [province, order_type, aux, target]
            return {
                "order_type": selected[1],
                "source": selected[0], 
                "target": selected[3],
                "aux": selected[2]
            }
        
        raise InvalidOrderStateException(f"Unable to convert order data: {selected}")