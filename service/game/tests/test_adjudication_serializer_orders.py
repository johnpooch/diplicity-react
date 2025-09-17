import pytest
from game import models
from game.serializers.adjudication_serializers import AdjudicationGameSerializer


@pytest.mark.django_db
class TestAdjudicationGameSerializerOrders:
    """Test the Orders field behavior in AdjudicationGameSerializer."""

    def test_orders_excludes_nations_with_no_orders(self, game_with_two_members):
        """Test that nations with no orders are excluded from Orders dict."""
        game = game_with_two_members
        phase = game.current_phase
        
        # Ensure phase states exist for both members
        for member in game.members.all():
            phase.phase_states.get_or_create(member=member)
        
        # Create units for both nations
        phase.units.create(type="Fleet", nation="England", province="lon")
        phase.units.create(type="Army", nation="France", province="par")
        
        # Only create orders for England
        england_phase_state = phase.phase_states.get(member__nation="England")
        england_phase_state.orders.create(order_type="Move", source="lon", target="eng")
        
        # France has no orders
        
        serializer = AdjudicationGameSerializer(game)
        orders = serializer.get_Orders(game)
        
        # Only England should be in the Orders dict
        assert "England" in orders
        assert "France" not in orders
        assert orders["England"]["lon"] == ["Move", "eng"]

    def test_orders_includes_all_nations_with_orders(self, game_with_two_members):
        """Test that all nations with orders are included."""
        game = game_with_two_members
        phase = game.current_phase
        
        # Ensure phase states exist for both members
        for member in game.members.all():
            phase.phase_states.get_or_create(member=member)
        
        # Create orders for both nations
        england_phase_state = phase.phase_states.get(member__nation="England")
        england_phase_state.orders.create(order_type="Hold", source="lon")
        
        france_phase_state = phase.phase_states.get(member__nation="France")
        france_phase_state.orders.create(order_type="Move", source="par", target="bur")
        
        serializer = AdjudicationGameSerializer(game)
        orders = serializer.get_Orders(game)
        
        # Both nations should be in the Orders dict
        assert "England" in orders
        assert "France" in orders
        assert orders["England"]["lon"] == ["Hold"]
        assert orders["France"]["par"] == ["Move", "bur"]

    def test_orders_empty_when_no_nation_has_orders(self, game_with_two_members):
        """Test that Orders dict is empty when no nation has orders."""
        game = game_with_two_members
        
        # No orders created for any nation
        
        serializer = AdjudicationGameSerializer(game)
        orders = serializer.get_Orders(game)
        
        # Orders dict should be empty
        assert orders == {}

    def test_orders_handles_multiple_orders_per_nation(self, game_with_two_members):
        """Test that multiple orders per nation are handled correctly."""
        game = game_with_two_members
        phase = game.current_phase
        
        # Create multiple orders for England
        england_phase_state = phase.phase_states.get(member__nation="England")
        england_phase_state.orders.create(order_type="Move", source="lon", target="eng")
        england_phase_state.orders.create(order_type="Support", source="lvp", target="lon", aux="eng")
        
        serializer = AdjudicationGameSerializer(game)
        orders = serializer.get_Orders(game)
        
        # England should have both orders
        assert "England" in orders
        assert "France" not in orders
        assert orders["England"]["lon"] == ["Move", "eng"]
        assert orders["England"]["lvp"] == ["Support", "lon", "eng"]

    def test_orders_handles_different_order_types(self, game_with_two_members):
        """Test that different order types are serialized correctly."""
        game = game_with_two_members
        phase = game.current_phase
        
        england_phase_state = phase.phase_states.get(member__nation="England")
        
        # Hold order (no target or aux)
        england_phase_state.orders.create(order_type="Hold", source="lon")
        
        # Move order (has target)
        england_phase_state.orders.create(order_type="Move", source="lvp", target="wal")
        
        # Support order (has target and aux)
        england_phase_state.orders.create(order_type="Support", source="edi", target="lvp", aux="wal")
        
        serializer = AdjudicationGameSerializer(game)
        orders = serializer.get_Orders(game)
        
        assert orders["England"]["lon"] == ["Hold"]
        assert orders["England"]["lvp"] == ["Move", "wal"]
        assert orders["England"]["edi"] == ["Support", "lvp", "wal"]