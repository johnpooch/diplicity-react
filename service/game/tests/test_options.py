import json
from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase
from game import models
from game.util import convert_decision_tree_to_options, UnknownProvinceError


class TestConvertDecisionTree(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.provinces = [
            {
                "id": "bud",
                "name": "Budapest",
                "supply_center": True,
                "type": "land"
            },
            {
                "id": "vie",
                "name": "Vienna",
                "supply_center": True,
                "type": "land"
            },
            {
                "id": "gal",
                "name": "Galicia",
                "supply_center": False,
                "type": "land"
            },
            {
                "id": "tri",
                "name": "Trieste",
                "supply_center": True,
                "type": "coastal"
            }
        ]

    def test_convert_hold_only(self):
        """Test converting a decision tree with only hold options"""
        decision_tree = {
            "bud": {
                "Next": {
                    "Hold": {
                        "Next": {},
                        "Type": "OrderType"
                    }
                },
                "Type": "Province"
            }
        }
        
        result = convert_decision_tree_to_options(decision_tree, self.provinces)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["province"], "bud")
        self.assertTrue(result[0]["hold"])
        self.assertEqual(result[0]["move"], [])
        self.assertIsNone(result[0]["support"])
        self.assertIsNone(result[0]["convoy"])

    def test_convert_move_options(self):
        """Test converting a decision tree with move options"""
        decision_tree = {
            "bud": {
                "Next": {
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"},
                                    "vie": {"Next": {}, "Type": "Province"}
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
        
        result = convert_decision_tree_to_options(decision_tree, self.provinces)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["province"], "bud")
        self.assertFalse(result[0]["hold"])
        
        moves = result[0]["move"]
        self.assertEqual(len(moves), 2)
        self.assertEqual(moves[0]["id"], "gal")
        self.assertEqual(moves[0]["name"], "Galicia")
        self.assertEqual(moves[1]["id"], "vie")
        self.assertEqual(moves[1]["name"], "Vienna")

    def test_convert_support_options(self):
        """Test converting a decision tree with support options"""
        decision_tree = {
            "bud": {
                "Next": {
                    "Support": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "vie": {
                                        "Next": {
                                            "tri": {"Next": {}, "Type": "Province"}
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
            }
        }
        
        result = convert_decision_tree_to_options(decision_tree, self.provinces)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["province"], "bud")
        self.assertFalse(result[0]["hold"])
        self.assertEqual(result[0]["move"], [])
        
        support = result[0]["support"]
        self.assertIsNotNone(support)
        self.assertEqual(support["from_province"]["id"], "vie")
        self.assertEqual(support["from_province"]["name"], "Vienna")
        self.assertEqual(support["to_province"]["id"], "tri")
        self.assertEqual(support["to_province"]["name"], "Trieste")

    def test_convert_multiple_options(self):
        """Test converting a decision tree with multiple types of options"""
        decision_tree = {
            "bud": {
                "Next": {
                    "Hold": {
                        "Next": {},
                        "Type": "OrderType"
                    },
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"}
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
        
        result = convert_decision_tree_to_options(decision_tree, self.provinces)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["province"], "bud")
        self.assertTrue(result[0]["hold"])
        
        moves = result[0]["move"]
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0]["id"], "gal")
        self.assertEqual(moves[0]["name"], "Galicia")

    def test_convert_unknown_province(self):
        """Test that converting a decision tree with an unknown province raises an error"""
        decision_tree = {
            "bud": {
                "Next": {
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "unknown": {"Next": {}, "Type": "Province"}
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
        
        with self.assertRaises(UnknownProvinceError) as context:
            convert_decision_tree_to_options(decision_tree, self.provinces)
        
        self.assertEqual(str(context.exception), "Province 'unknown' not found in provided provinces list")
