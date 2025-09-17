import pytest
from game.services.options_service import OptionsService, InvalidOrderStateException


class MockVariant:
    """Mock variant for testing"""
    def __init__(self):
        self.provinces = [
            {"id": "bud", "name": "Budapest"},
            {"id": "tri", "name": "Trieste"}, 
            {"id": "vie", "name": "Vienna"},
            {"id": "gal", "name": "Galicia"},
            {"id": "rum", "name": "Rumania"},
            {"id": "ser", "name": "Serbia"},
            {"id": "sev", "name": "Sevastopol"},
            {"id": "war", "name": "Warsaw"},
            {"id": "ven", "name": "Venice"},
            {"id": "adr", "name": "Adriatic Sea"},
            {"id": "alb", "name": "Albania"},
            {"id": "boh", "name": "Bohemia"},
            {"id": "tyr", "name": "Tyrolia"},
            {"id": "mun", "name": "Munich"},
            {"id": "rom", "name": "Rome"}
        ]


@pytest.fixture
def mock_variant():
    return MockVariant()


@pytest.fixture
def sample_options():
    """Sample options data based on the test data"""
    return {
        "England": {
            "bud": {
                "Next": {
                    "Hold": {
                        "Next": {
                            "bud": {
                                "Next": {},
                                "Type": "SrcProvince"
                            }
                        },
                        "Type": "OrderType"
                    },
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"},
                                    "rum": {"Next": {}, "Type": "Province"},
                                    "ser": {"Next": {}, "Type": "Province"},
                                    "tri": {"Next": {}, "Type": "Province"},
                                    "vie": {"Next": {}, "Type": "Province"}
                                },
                                "Type": "SrcProvince"
                            }
                        },
                        "Type": "OrderType"
                    },
                    "Support": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "sev": {
                                        "Next": {
                                            "rum": {"Next": {}, "Type": "Province"}
                                        },
                                        "Type": "Province"
                                    },
                                    "tri": {
                                        "Next": {
                                            "tri": {"Next": {}, "Type": "Province"}
                                        },
                                        "Type": "Province"
                                    },
                                    "vie": {
                                        "Next": {
                                            "gal": {"Next": {}, "Type": "Province"},
                                            "tri": {"Next": {}, "Type": "Province"},
                                            "vie": {"Next": {}, "Type": "Province"}
                                        },
                                        "Type": "Province"
                                    }
                                },
                                "Type": "SrcProvince"
                            }
                        },
                        "Type": "OrderType"
                    }
                },
                "Type": "Province"
            },
            "vie": {
                "Next": {
                    "Hold": {
                        "Next": {
                            "vie": {"Next": {}, "Type": "SrcProvince"}
                        },
                        "Type": "OrderType"
                    },
                    "Move": {
                        "Next": {
                            "vie": {
                                "Next": {
                                    "boh": {"Next": {}, "Type": "Province"},
                                    "bud": {"Next": {}, "Type": "Province"},
                                    "gal": {"Next": {}, "Type": "Province"},
                                    "tri": {"Next": {}, "Type": "Province"},
                                    "tyr": {"Next": {}, "Type": "Province"}
                                },
                                "Type": "SrcProvince"
                            }
                        },
                        "Type": "OrderType"
                    }
                },
                "Type": "Province"
            }
        }
    }


@pytest.fixture
def options_service(sample_options, mock_variant):
    return OptionsService(sample_options, mock_variant)


class TestOptionsServiceInitialization:
    def test_init_with_valid_data(self, sample_options, mock_variant):
        service = OptionsService(sample_options, mock_variant)
        assert service.options == sample_options
        assert service.variant == mock_variant
        assert len(service.province_lookup) == len(mock_variant.provinces)
    
    def test_province_lookup_creation(self, sample_options, mock_variant):
        service = OptionsService(sample_options, mock_variant)
        assert service.province_lookup["bud"]["name"] == "Budapest"
        assert service.province_lookup["tri"]["name"] == "Trieste"


class TestListOptionsForNation:
    def test_valid_nation(self, options_service):
        provinces = options_service.list_options_for_nation("England")
        assert "bud" in provinces
        assert "vie" in provinces
        assert len(provinces) == 2
    
    def test_invalid_nation(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Nation 'France' not found in options"):
            options_service.list_options_for_nation("France")


class TestListOptionsForSelected:
    def test_empty_selected_raises_exception(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Selected options cannot be empty"):
            options_service.list_options_for_selected("England", [])
    
    def test_invalid_nation(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Nation 'France' not found in options"):
            options_service.list_options_for_selected("France", ["bud"])
    
    def test_province_selected_shows_order_types(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud"])
        
        assert result["step"] == "select-order-type"
        assert result["title"] == "Select order type for Budapest"
        assert not result["completed"]
        assert not result["can_go_back"]  # Cannot go back from order type selection
        
        order_types = [opt["value"] for opt in result["options"]]
        assert "Hold" in order_types
        assert "Move" in order_types
        assert "Support" in order_types
    
    def test_invalid_province(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Province 'invalid' not available for nation 'England'"):
            options_service.list_options_for_selected("England", ["invalid"])
    
    def test_hold_order_completion(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Hold"])
        
        assert result["step"] == "completed"
        assert result["title"] == "Budapest will hold"
        assert result["completed"]
        assert not result["can_go_back"]
        assert len(result["options"]) == 0
    
    def test_move_order_target_selection(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Move"])
        
        assert result["step"] == "select-destination"
        assert result["title"] == "Select province to move Budapest to"
        assert not result["completed"]
        assert result["can_go_back"]
        
        targets = [opt["value"] for opt in result["options"]]
        assert "gal" in targets
        assert "rum" in targets
        assert "tri" in targets
    
    def test_move_order_completion(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Move", "tri"])
        
        assert result["step"] == "completed"
        assert result["title"] == "Budapest will move to Trieste"
        assert result["completed"]
        assert not result["can_go_back"]
        assert len(result["options"]) == 0
    
    def test_support_order_auxiliary_selection(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Support"])
        
        assert result["step"] == "select-auxiliary"
        assert result["title"] == "Select province to support for Budapest"
        assert not result["completed"]
        assert result["can_go_back"]
        
        aux_options = [opt["value"] for opt in result["options"]]
        assert "sev" in aux_options
        assert "tri" in aux_options
        assert "vie" in aux_options
    
    def test_support_order_target_selection(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Support", "vie"])
        
        assert result["step"] == "select-target"
        assert result["title"] == "Select target for support order"
        assert not result["completed"]
        assert result["can_go_back"]
        
        targets = [opt["value"] for opt in result["options"]]
        assert "gal" in targets
        assert "tri" in targets
        assert "vie" in targets
    
    def test_support_order_completion(self, options_service):
        result = options_service.list_options_for_selected("England", ["bud", "Support", "vie", "tri"])
        
        assert result["step"] == "completed"
        assert result["title"] == "Budapest will support Vienna to Trieste"
        assert result["completed"]
        assert not result["can_go_back"]
        assert len(result["options"]) == 0
    
    def test_invalid_order_type(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Order type 'InvalidType' not available for province 'bud'"):
            options_service.list_options_for_selected("England", ["bud", "InvalidType"])
    
    def test_invalid_move_target(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid move target 'invalid' for province 'bud'"):
            options_service.list_options_for_selected("England", ["bud", "Move", "invalid"])
    
    def test_invalid_support_auxiliary(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid auxiliary province 'invalid' for Support from 'bud'"):
            options_service.list_options_for_selected("England", ["bud", "Support", "invalid"])
    
    def test_invalid_support_target(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid support order"):
            options_service.list_options_for_selected("England", ["bud", "Support", "vie", "invalid"])
    
    def test_invalid_selection_length(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid selection length: 5 items"):
            options_service.list_options_for_selected("England", ["bud", "Move", "tri", "extra", "invalid"])


class TestValidateCompleteOrder:
    def test_valid_hold_order(self, options_service):
        assert options_service.validate_complete_order("England", ["bud", "Hold"])
    
    def test_valid_move_order(self, options_service):
        assert options_service.validate_complete_order("England", ["bud", "Move", "tri"])
    
    def test_valid_support_order(self, options_service):
        assert options_service.validate_complete_order("England", ["bud", "Support", "vie", "tri"])
    
    def test_incomplete_move_order(self, options_service):
        assert not options_service.validate_complete_order("England", ["bud", "Move"])
    
    def test_incomplete_support_order(self, options_service):
        assert not options_service.validate_complete_order("England", ["bud", "Support"])
        assert not options_service.validate_complete_order("England", ["bud", "Support", "vie"])
    
    def test_invalid_order(self, options_service):
        assert not options_service.validate_complete_order("England", ["bud", "InvalidType"])
        assert not options_service.validate_complete_order("France", ["bud", "Hold"])


class TestConvertToOrderData:
    def test_convert_hold_order(self, options_service):
        order_data = options_service.convert_to_order_data("England", ["bud", "Hold"])
        
        assert order_data["order_type"] == "Hold"
        assert order_data["source"] == "bud"
        assert order_data["target"] is None
        assert order_data["aux"] is None
    
    def test_convert_move_order(self, options_service):
        order_data = options_service.convert_to_order_data("England", ["bud", "Move", "tri"])
        
        assert order_data["order_type"] == "Move"
        assert order_data["source"] == "bud"
        assert order_data["target"] == "tri"
        assert order_data["aux"] is None
    
    def test_convert_support_order(self, options_service):
        order_data = options_service.convert_to_order_data("England", ["bud", "Support", "vie", "tri"])
        
        assert order_data["order_type"] == "Support"
        assert order_data["source"] == "bud"
        assert order_data["target"] == "tri"
        assert order_data["aux"] == "vie"
    
    def test_convert_incomplete_order(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid or incomplete order"):
            options_service.convert_to_order_data("England", ["bud", "Move"])
    
    def test_convert_invalid_order(self, options_service):
        with pytest.raises(InvalidOrderStateException, match="Invalid or incomplete order"):
            options_service.convert_to_order_data("England", ["bud", "InvalidType"])


class TestProvinceDisplayNames:
    def test_province_display_name_lookup(self, options_service):
        assert options_service._get_province_display_name("bud") == "Budapest"
        assert options_service._get_province_display_name("tri") == "Trieste"
        assert options_service._get_province_display_name("vie") == "Vienna"
    
    def test_province_display_name_fallback(self, options_service):
        # Test fallback for unknown province
        assert options_service._get_province_display_name("unknown") == "Unknown"
    
    def test_display_names_in_options(self, options_service):
        # Test that display names are used in the options
        result = options_service.list_options_for_selected("England", ["bud"])
        assert result["title"] == "Select order type for Budapest"
        
        result = options_service.list_options_for_selected("England", ["bud", "Move"])
        target_labels = [opt["label"] for opt in result["options"]]
        assert "Trieste" in target_labels
        assert "Vienna" in target_labels