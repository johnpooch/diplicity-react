import pytest
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from game import models
from game.services.game_service import GameService


@pytest.fixture
def mock_adjudication_service_no_moves():
    """Mock adjudication service that returns no valid moves."""
    mock = MagicMock()
    mock.resolve.return_value = {
        "phase": {
            "season": "Fall",
            "year": 1901,
            "type": "Adjustment",
            "resolutions": [],
            "units": [],
            "supply_centers": []
        },
        "options": {}  # No valid moves for any nation
    }
    return mock


@pytest.fixture
def mock_adjudication_service_empty_nations():
    """Mock adjudication service that returns empty nation options."""
    mock = MagicMock()
    mock.resolve.return_value = {
        "phase": {
            "season": "Fall", 
            "year": 1901,
            "type": "Adjustment",
            "resolutions": [],
            "units": [],
            "supply_centers": []
        },
        "options": {
            "England": {},
            "France": {},
            "Germany": {}
        }
    }
    return mock


@pytest.fixture
def mock_adjudication_service_with_valid_moves():
    """Mock adjudication service that returns valid moves."""
    mock = MagicMock()
    mock.resolve.return_value = {
        "phase": {
            "season": "Fall",
            "year": 1901, 
            "type": "Movement",
            "resolutions": [],
            "units": [],
            "supply_centers": []
        },
        "options": {
            "England": {
                "lon": {
                    "Next": {
                        "Hold": {},
                        "Move": {"Next": {"eng": {"Next": {}}}}
                    }
                }
            }
        }
    }
    return mock


class TestHasNoValidMoves:
    """Test the _has_no_valid_moves helper method."""
    
    def test_empty_options_data(self, primary_user):
        """Test empty options data returns True."""
        service = GameService(primary_user)
        assert service._has_no_valid_moves({}) is True
        assert service._has_no_valid_moves(None) is True
    
    def test_nations_with_empty_options(self, primary_user):
        """Test nations with empty province options returns True."""
        service = GameService(primary_user)
        options_data = {
            "England": {},
            "France": {},
            "Germany": {}
        }
        assert service._has_no_valid_moves(options_data) is True
    
    def test_nations_with_valid_moves(self, primary_user):
        """Test nations with valid moves returns False."""
        service = GameService(primary_user)
        options_data = {
            "England": {
                "lon": {
                    "Next": {
                        "Hold": {},
                        "Move": {"Next": {"eng": {"Next": {}}}}
                    }
                }
            },
            "France": {}
        }
        assert service._has_no_valid_moves(options_data) is False
    
    def test_mixed_valid_and_empty_nations(self, primary_user):
        """Test that if any nation has moves, returns False."""
        service = GameService(primary_user)
        options_data = {
            "England": {},
            "France": {
                "par": {
                    "Next": {
                        "Hold": {}
                    }
                }
            }
        }
        assert service._has_no_valid_moves(options_data) is False
    
    def test_invalid_options_structure(self, primary_user):
        """Test invalid options structure returns True."""
        service = GameService(primary_user)
        assert service._has_no_valid_moves("invalid") is True
        assert service._has_no_valid_moves(123) is True


@pytest.mark.django_db
class TestPhaseCreationWithNoMoves:
    """Test phase creation behavior when there are no valid moves."""
    
    def test_create_phase_with_no_moves_schedules_immediate_resolution(
        self, primary_user, classical_variant
    ):
        """Test that phases with no valid moves get scheduled for immediate resolution."""
        service = GameService(primary_user)
        
        game = models.Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=models.Game.ACTIVE
        )
        
        phase_data = {
            "season": "Fall",
            "year": 1901,
            "type": "Adjustment",
            "units": [],
            "supply_centers": []
        }
        
        options_data = {}  # No valid moves
        
        # Record current time before creating phase
        before_time = timezone.now()
        
        phase = service._create_phase(game, phase_data, options_data)
        
        after_time = timezone.now()
        
        # Should have scheduled resolution set to approximately now
        assert phase.scheduled_resolution is not None
        assert before_time <= phase.scheduled_resolution <= after_time
    
    def test_create_phase_with_valid_moves_does_not_schedule_immediate_resolution(
        self, primary_user, classical_variant
    ):
        """Test that phases with valid moves do not get immediate resolution."""
        service = GameService(primary_user)
        
        game = models.Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=models.Game.ACTIVE
        )
        
        phase_data = {
            "season": "Spring",
            "year": 1901,
            "type": "Movement", 
            "units": [],
            "supply_centers": []
        }
        
        options_data = {
            "England": {
                "lon": {
                    "Next": {
                        "Hold": {},
                        "Move": {"Next": {"eng": {"Next": {}}}}
                    }
                }
            }
        }
        
        phase = service._create_phase(game, phase_data, options_data)
        
        # Should not have scheduled resolution set
        assert phase.scheduled_resolution is None


@pytest.mark.django_db  
class TestGameResolveWithNoMoves:
    """Test full game resolution flow when next phase has no valid moves."""
    
    def test_resolve_creates_phase_with_immediate_resolution_when_no_moves(
        self, primary_user, active_game_with_phase_state, mock_adjudication_service_no_moves
    ):
        """Test that resolving creates a phase scheduled for immediate resolution when no moves."""
        game = active_game_with_phase_state
        
        service = GameService(primary_user, mock_adjudication_service_no_moves)
        
        before_time = timezone.now()
        
        with patch('game.services.notification_service.NotificationService.notify'):
            resolved_game = service.resolve(game.id)
            
        after_time = timezone.now()
        
        # Should have created a new phase with immediate resolution
        latest_phase = resolved_game.phases.last()
        assert latest_phase.scheduled_resolution is not None
        assert before_time <= latest_phase.scheduled_resolution <= after_time
        assert latest_phase.options_dict == {}
    
    def test_resolve_creates_phase_without_immediate_resolution_when_has_moves(
        self, primary_user, active_game_with_phase_state, mock_adjudication_service_with_valid_moves
    ):
        """Test that resolving creates normal phase when there are valid moves."""
        game = active_game_with_phase_state
        
        service = GameService(primary_user, mock_adjudication_service_with_valid_moves)
        
        before_time = timezone.now()
        
        with patch('game.services.notification_service.NotificationService.notify'):
            resolved_game = service.resolve(game.id)
            
        after_time = timezone.now()
        
        # Should have created a new phase with normal 24-hour resolution schedule
        latest_phase = resolved_game.phases.last()
        assert latest_phase.scheduled_resolution is not None
        # Should be scheduled 24 hours from now (not immediate)
        expected_min_time = before_time + timedelta(hours=24)
        expected_max_time = after_time + timedelta(hours=24)
        assert expected_min_time <= latest_phase.scheduled_resolution <= expected_max_time
        assert latest_phase.options_dict != {}
    
    def test_resolve_with_empty_nation_options_schedules_immediate_resolution(
        self, primary_user, active_game_with_phase_state, mock_adjudication_service_empty_nations
    ):
        """Test that phases with empty nation options get immediate resolution."""
        game = active_game_with_phase_state
        
        service = GameService(primary_user, mock_adjudication_service_empty_nations)
        
        before_time = timezone.now()
        
        with patch('game.services.notification_service.NotificationService.notify'):
            resolved_game = service.resolve(game.id)
            
        after_time = timezone.now()
        
        latest_phase = resolved_game.phases.last()
        assert latest_phase.scheduled_resolution is not None
        assert before_time <= latest_phase.scheduled_resolution <= after_time
        assert latest_phase.options_dict == {"England": {}, "France": {}, "Germany": {}}