import json
from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase
from game import models
from game.serializers.options_serializer import convert_decision_tree_to_options, UnknownProvinceError


class TestOptionsRetrieve(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create an active game with a phase
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.phase = self.game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
        )
        self.member = self.game.members.first()
        
        # Create a phase state with some options
        self.options_data = {
            "bud": {"Next": {"Hold": {"Next": {}, "Type": "OrderType"}}}
        }
        self.phase_state = models.PhaseState.objects.create(
            member=self.member,
            phase=self.phase,
            options=json.dumps(self.options_data)
        )

    def create_request(self, game_id):
        url = reverse("options-retrieve", args=[game_id])
        return self.client.get(url)

    def test_retrieve_options_authenticated_member(self):
        """Test that an authenticated game member can retrieve their options"""
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['options'], self.options_data)

    def test_retrieve_options_non_member(self):
        """Test that a non-member gets null options"""
        other_user = self.create_user("other_user", "password")
        self.client.force_authenticate(user=other_user)
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['options'])

    def test_retrieve_options_inactive_game(self):
        """Test that an inactive game returns an error"""
        self.game.status = models.Game.PENDING
        self.game.save()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_options_unauthenticated(self):
        """Test that an unauthenticated user cannot retrieve options"""
        self.client.logout()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_options_nonexistent_game(self):
        """Test that a nonexistent game returns a 404"""
        response = self.create_request(999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_options_no_phase_state(self):
        """Test retrieving options when there's no phase state"""
        self.phase_state.delete()
        response = self.create_request(self.game.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['options'])


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
