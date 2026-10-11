import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from jsonschema import Draft7Validator, ValidationError

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "specs" / "workout_schema.json"


def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the JSON schema contract for workouts."""
    path = schema_path or DEFAULT_SCHEMA_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_workout(data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate a workout dictionary against the WorkoutSpec schema.

    Returns:
        (True, None) if valid.
        (False, error_message) if invalid.
    """
    spec_schema = schema or load_schema()
    validator = Draft7Validator(spec_schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    
    if not errors:
        return True, None

    first_error = errors[0]
    error_path = " -> ".join(str(p) for p in first_error.path) if first_error.path else "root"
    message = f"Schema error at [{error_path}]: {first_error.message}"
    return False, message
