from django.db import models

from .base import BaseModel


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)
    nations_data = models.JSONField()
    start_data = models.JSONField()
    provinces_data = models.JSONField()

    @property
    def nations(self):
        return self.nations_data

    @property
    def start(self):
        return self.start_data

    @property
    def provinces(self):
        return self.provinces_data

    @property
    def initial_phase(self):
        """Convert the variant's start data into a phase-like structure"""
        start_data = self.start
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
