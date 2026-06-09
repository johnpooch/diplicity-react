from variant.utils import _validate_dvar_phase_progression


CLASSICAL_PHASE_PROGRESSION = {
    "seasons": ["Spring", "Fall"],
    "transitions": [
        {"from": {"type": "Movement", "season": "Spring"}, "to": {"type": "Retreat", "season": "Spring", "yearDelta": 0}},
        {"from": {"type": "Retreat", "season": "Spring"}, "to": {"type": "Movement", "season": "Fall", "yearDelta": 0}},
        {"from": {"type": "Movement", "season": "Fall"}, "to": {"type": "Retreat", "season": "Fall", "yearDelta": 0}},
        {"from": {"type": "Retreat", "season": "Fall"}, "to": {"type": "Adjustment", "season": "Fall", "yearDelta": 0}},
        {"from": {"type": "Adjustment", "season": "Fall"}, "to": {"type": "Movement", "season": "Spring", "yearDelta": 1}},
    ],
}


def test_classical_progression_is_valid():
    errors = _validate_dvar_phase_progression({"phaseProgression": CLASSICAL_PHASE_PROGRESSION})
    assert errors == []


def test_ambiguous_unconditional_transitions():
    dvar = {
        "phaseProgression": {
            "seasons": ["Movement A", "Retreat", "Movement B", "Build"],
            "transitions": [
                {"from": {"type": "Movement", "season": "Movement A"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Movement", "season": "Movement B", "yearDelta": 0}},
                {"from": {"type": "Movement", "season": "Movement B"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Adjustment", "season": "Build", "yearDelta": 0}},
                {"from": {"type": "Adjustment", "season": "Build"}, "to": {"type": "Movement", "season": "Movement A", "yearDelta": 60}},
            ],
        }
    }
    errors = _validate_dvar_phase_progression(dvar)
    assert len(errors) == 1
    assert errors[0].code == "AMBIGUOUS_TRANSITION"
    assert "1 and 3" in errors[0].message


def test_conditional_transitions_with_same_from_are_valid():
    dvar = {
        "phaseProgression": {
            "seasons": ["Movement A", "Retreat", "Movement B", "Build"],
            "transitions": [
                {"from": {"type": "Movement", "season": "Movement A"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Movement", "season": "Movement B", "yearDelta": 0}, "condition": {"yearMod": 100, "yearModValue": 20}},
                {"from": {"type": "Movement", "season": "Movement B"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Adjustment", "season": "Build", "yearDelta": 0}, "condition": {"yearMod": 100, "yearModValue": 40}},
                {"from": {"type": "Adjustment", "season": "Build"}, "to": {"type": "Movement", "season": "Movement A", "yearDelta": 60}},
            ],
        }
    }
    errors = _validate_dvar_phase_progression(dvar)
    assert errors == []


def test_one_conditional_one_unconditional_is_valid():
    dvar = {
        "phaseProgression": {
            "seasons": ["Movement A", "Retreat", "Movement B", "Build"],
            "transitions": [
                {"from": {"type": "Movement", "season": "Movement A"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Movement", "season": "Movement B", "yearDelta": 0}},
                {"from": {"type": "Movement", "season": "Movement B"}, "to": {"type": "Retreat", "season": "Retreat", "yearDelta": 20}},
                {"from": {"type": "Retreat", "season": "Retreat"}, "to": {"type": "Adjustment", "season": "Build", "yearDelta": 0}, "condition": {"yearMod": 100, "yearModValue": 40}},
                {"from": {"type": "Adjustment", "season": "Build"}, "to": {"type": "Movement", "season": "Movement A", "yearDelta": 60}},
            ],
        }
    }
    errors = _validate_dvar_phase_progression(dvar)
    assert errors == []


def test_missing_phase_progression():
    errors = _validate_dvar_phase_progression({})
    assert errors == []
