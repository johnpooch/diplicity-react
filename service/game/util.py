from rest_framework import serializers
from typing import Dict, Any, List

def create_serializer_class(name, fields, extra_methods=None):
    extra_methods = extra_methods or {}
    return type(name, (serializers.Serializer,), {**fields, **extra_methods})


def inline_serializer(
    *, fields, data=None, extra_methods=None, name="DynamicSerializer", **kwargs
):
    serializer_class = create_serializer_class(
        name=name, fields=fields, extra_methods=extra_methods
    )

    if data is not None:
        return serializer_class(data=data, **kwargs)

    return serializer_class(**kwargs)


class UnknownProvinceError(Exception):
    """Raised when a province in the decision tree is not found in the provided provinces list."""
    pass

def convert_decision_tree_to_options(decision_tree: Dict[str, Any], provinces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert the decision tree format into a list of options compatible with OptionsSerializer.
    
    Args:
        decision_tree: The decision tree structure from options.json
        provinces: List of province definitions from the variant file
        
    Returns:
        List of dictionaries compatible with OptionsSerializer
        
    Raises:
        UnknownProvinceError: If a province in the decision tree is not found in the provinces list
    """
    # Create a lookup dictionary for province names
    province_names = {p["id"]: p["name"] for p in provinces}
    
    def validate_province(province_id: str) -> str:
        """Helper function to validate and return province name"""
        if province_id not in province_names:
            raise UnknownProvinceError(f"Province '{province_id}' not found in provided provinces list")
        return province_names[province_id]
    
    options_list = []
    
    for province, province_data in decision_tree.items():
        # Validate the main province
        validate_province(province)
        
        if "Next" not in province_data:
            continue
            
        options = {
            "province": province,
            "hold": False,
            "move": [],
            "support": None,
            "convoy": None
        }
        
        next_data = province_data["Next"]
        
        # Process Hold
        if "Hold" in next_data:
            options["hold"] = True
            
        # Process Move
        if "Move" in next_data:
            move_provinces = next_data["Move"]["Next"].get(province, {}).get("Next", {})
            options["move"] = [
                {"id": dest_province, "name": validate_province(dest_province)}
                for dest_province in move_provinces.keys()
            ]
            
        # Process Support
        if "Support" in next_data:
            support_data = next_data["Support"]["Next"].get(province, {}).get("Next", {})
            if support_data:
                # Take the first support option as an example
                from_province = next(iter(support_data))
                to_provinces = next(iter(support_data.values()))["Next"]
                if to_provinces:
                    to_province = next(iter(to_provinces))
                    options["support"] = {
                        "from_province": {
                            "id": from_province,
                            "name": validate_province(from_province)
                        },
                        "to_province": {
                            "id": to_province,
                            "name": validate_province(to_province)
                        }
                    }
        
        options_list.append(options)
    
    return options_list