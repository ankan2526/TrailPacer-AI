import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import requests
from jsonschema import validate, ValidationError

from src.validator import load_schema, validate_workout

import os

SPEC_PATH = Path(__file__).resolve().parent.parent / "specs" / "workout_schema.json"
FALLBACK_PATH = Path(__file__).resolve().parent.parent / "specs" / "fallback_workouts.json"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("TRAILPACER_MODEL", "qwen2.5:0.5b")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrailPacer")


def load_fallback_workout(activity: str) -> Dict[str, Any]:
    """Retrieve pre-spec cached workout from disk on inference or validation failure."""
    if FALLBACK_PATH.exists():
        with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
            fallbacks = json.load(f)
            if activity in fallbacks:
                return fallbacks[activity]
            # default to first available fallback
            return next(iter(fallbacks.values()))
    
    # Minimal hardcoded fallback if file missing
    return {
        "title": "Default Trail Recovery",
        "activity_type": activity if activity in ["trail_walk", "fartlek_run", "rucking", "interval_sprints"] else "trail_walk",
        "target_duration_minutes": 30,
        "terrain_suggestion": "Flat or gently rolling trail",
        "blocks": [
            {
                "phase": "warmup",
                "duration_minutes": 5,
                "instruction": "Easy conversational warm-up pace",
                "target_rpe_1_to_10": 2
            },
            {
                "phase": "main_set",
                "duration_minutes": 20,
                "instruction": "Steady continuous aerobic effort",
                "target_rpe_1_to_10": 5
            },
            {
                "phase": "cooldown",
                "duration_minutes": 5,
                "instruction": "Slow walk and recovery stretch",
                "target_rpe_1_to_10": 2
            }
        ]
    }


def call_local_llm(prompt: str, schema: Optional[Dict[str, Any]] = None, temperature: Optional[float] = None, timeout: int = 25) -> str:
    """Send request to local Ollama inference endpoint."""
    options = {}
    if temperature is not None:
        options["temperature"] = temperature

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": schema if schema else "json"
    }
    if options:
        payload["options"] = options

    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def generate_workout(
    activity: str,
    duration: int,
    fitness_level: str,
    max_retries: int = 2,
    use_fallback_on_error: bool = True
) -> Dict[str, Any]:
    """
    Generate an offline outdoor workout routine adhering to workout_schema.json.
    
    Implements retry strategy (temperature=0.1) and fallback cache per functional spec.
    """
    schema = load_schema(SPEC_PATH)
    
    base_prompt = f"""You are TrailPacer AI, an offline outdoor coach.
Generate a {duration}-minute {activity} workout for a {fitness_level} fitness level.

IMPORTANT: You MUST include ALL required fields:
- "title": string
- "activity_type": "{activity}"
- "target_duration_minutes": {duration}
- "terrain_suggestion": descriptive string
- "blocks": array with at least 2 blocks containing "phase", "duration_minutes", "instruction", and "target_rpe_1_to_10".

Return ONLY the raw JSON object conforming strictly to the schema."""

    current_prompt = base_prompt
    temperature = None

    for attempt in range(max_retries + 1):
        try:
            logger.info("Requesting workout generation (attempt %d/%d)...", attempt + 1, max_retries + 1)
            raw_response = call_local_llm(current_prompt, schema=schema, temperature=temperature)
            workout_data = json.loads(raw_response)

            
            # Enforce Spec Compliance
            is_valid, error_msg = validate_workout(workout_data, schema=schema)
            if is_valid:
                logger.info("Workout successfully validated against schema.")
                return workout_data
            
            logger.warning("Schema validation failed: %s", error_msg)
            # Constrain temperature on retries per FR spec
            temperature = 0.1
            current_prompt = (
                f"{base_prompt}\n\n"
                f"PREVIOUS ATTEMPT FAILED SCHEMA VALIDATION: {error_msg}\n"
                f"Fix the error and return valid JSON adhering strictly to the schema."
            )

        except (requests.RequestException, json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Inference or parse error during attempt %d: %s", attempt + 1, exc)
            temperature = 0.1

    if use_fallback_on_error:
        logger.warning("Local inference failed or exhausted retries. Serving pre-spec fallback workout.")
        fallback = load_fallback_workout(activity)
        # Validate fallback to ensure guaranteed compliance
        validate(instance=fallback, schema=schema)
        return fallback

    raise RuntimeError("Failed to generate a spec-compliant workout after retries.")


if __name__ == "__main__":
    import sys
    act = sys.argv[1] if len(sys.argv) > 1 else "fartlek_run"
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    level = sys.argv[3] if len(sys.argv) > 3 else "intermediate"

    result = generate_workout(act, dur, level)
    print(json.dumps(result, indent=2))
