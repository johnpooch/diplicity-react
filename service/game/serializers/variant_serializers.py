from rest_framework import serializers


class ProvinceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    supply_center = serializers.BooleanField()


class NationSerializer(serializers.Serializer):
    name = serializers.CharField()
    color = serializers.CharField()


class StartSerializer(serializers.Serializer):
    season = serializers.CharField()
    year = serializers.CharField()
    type = serializers.CharField()
    units = serializers.ListField(child=serializers.DictField())
    supply_centers = serializers.ListField(child=serializers.DictField())


class VariantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    author = serializers.CharField(required=False)
    nations = NationSerializer(many=True)
    start = StartSerializer()
    provinces = ProvinceSerializer(many=True)
    initial_phase = serializers.SerializerMethodField()

    def get_initial_phase(self, obj):
        """Convert the variant's start data into a phase-like structure"""
        start_data = obj.start
        if not start_data:
            return None
            
        # Create a synthetic phase from the start data
        initial_phase = {
            'id': 0,
            'ordinal': 1,
            'season': start_data['season'],
            'year': start_data['year'],
            'name': f"{start_data['season']} {start_data['year']}, {start_data['type']}",
            'type': start_data['type'],
            'remaining_time': None,
            'units': [],
            'supply_centers': [],
            'options': {},
            'status': 'pending'
        }
        
        # Convert units
        for unit_data in start_data.get('units', []):
            unit = {
                'type': unit_data['type'],
                'nation': {'name': unit_data['nation']},
                'province': {
                    'id': unit_data['province'],
                    'name': unit_data['province'],
                    'type': 'land',  # Default assumption
                    'supply_center': False
                }
            }
            initial_phase['units'].append(unit)
        
        # Convert supply centers
        for sc_data in start_data.get('supply_centers', []):
            supply_center = {
                'province': {
                    'id': sc_data['province'],
                    'name': sc_data['province'],
                    'type': 'land',  # Default assumption
                    'supply_center': True
                },
                'nation': {'name': sc_data['nation']}
            }
            initial_phase['supply_centers'].append(supply_center)
        
        return initial_phase
