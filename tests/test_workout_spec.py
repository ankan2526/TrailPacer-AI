import json
from pathlib import Path
import pytest
from jsonschema import validate, ValidationError

from src.validator import load_schema, validate_workout


@pytest.fixture
def schema():
    spec_path = Path(__file__).resolve().parent.parent / "specs" / "workout_schema.json"
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_workout_structure(schema):
    sample_output = {
        "title": "Morning Trail Fartlek",
        "activity_type": "fartlek_run",
        "target_duration_minutes": 30,
        "terrain_suggestion": "Rolling dirt trails or park path",
        "blocks": [
            {
                "phase": "warmup",
                "duration_minutes": 5,
                "instruction": "Easy jog with arm circles",
                "target_rpe_1_to_10": 3
            },
            {
                "phase": "main_set",
                "duration_minutes": 20,
                "instruction": "Surge for 1 min every landmark reached",
                "target_rpe_1_to_10": 7
            },
            {
                "phase": "cooldown",
                "duration_minutes": 5,
                "instruction": "Brisk walk and quad stretches",
                "target_rpe_1_to_10": 2
            }
        ]
    }
    # Should complete without throwing ValidationError
    validate(instance=sample_output, schema=schema)
    is_valid, err = validate_workout(sample_output, schema=schema)
    assert is_valid is True
    assert err is None


def test_invalid_activity_type(schema):
    sample_output = {
        "title": "Road Ride",
        "activity_type": "cycling",  # Not in enum
        "target_duration_minutes": 30,
        "terrain_suggestion": "Paved road",
        "blocks": [
            {
                "phase": "warmup",
                "duration_minutes": 5,
                "instruction": "Easy spin",
                "target_rpe_1_to_10": 2
            },
            {
                "phase": "main_set",
                "duration_minutes": 25,
                "instruction": "Hard tempo",
                "target_rpe_1_to_10": 7
            }
        ]
    }
    with pytest.raises(ValidationError):
        validate(instance=sample_output, schema=schema)
    is_valid, err = validate_workout(sample_output, schema=schema)
    assert is_valid is False
    assert err is not None


def test_missing_required_field(schema):
    sample_output = {
        "title": "Incomplete Routine",
        "activity_type": "trail_walk",
        # missing target_duration_minutes
        "terrain_suggestion": "Gravel path",
        "blocks": [
            {
                "phase": "warmup",
                "duration_minutes": 5,
                "instruction": "Walk",
                "target_rpe_1_to_10": 2
            },
            {
                "phase": "main_set",
                "duration_minutes": 20,
                "instruction": "Power walk",
                "target_rpe_1_to_10": 5
            }
        ]
    }
    with pytest.raises(ValidationError):
        validate(instance=sample_output, schema=schema)


def test_fallback_workouts_conform_to_schema(schema):
    fallback_path = Path(__file__).resolve().parent.parent / "specs" / "fallback_workouts.json"
    with open(fallback_path, "r", encoding="utf-8") as f:
        fallbacks = json.load(f)
    
    assert len(fallbacks) >= 4
    for activity_name, workout in fallbacks.items():
        validate(instance=workout, schema=schema)
        is_valid, err = validate_workout(workout, schema=schema)
        assert is_valid is True, f"Fallback for {activity_name} failed validation: {err}"


def test_agent_fallback_generation(schema):
    from src.agent import generate_workout
    # When local inference cannot connect, it should fall back to valid workout data
    workout = generate_workout("trail_walk", 30, "beginner", max_retries=0, use_fallback_on_error=True)
    validate(instance=workout, schema=schema)
    assert workout["activity_type"] == "trail_walk"

