# Functional Specification: TrailPacer AI

## 1. Goal
Generate structured outdoor workout routines offline using open-weight models, minimizing screen interaction time to under 15 seconds.

## 2. Core Requirements
- **FR-1:** System must run 100% offline via local inference (Ollama/llama.cpp).
- **FR-2:** Output must strictly adhere to `specs/workout_schema.json`.
- **FR-3:** Total workout generation time must remain under 5 seconds on CPU/Apple Silicon.
- **FR-4:** Supported activity types: `trail_walk`, `fartlek_run`, `rucking`, `interval_sprints`.

## 3. Error Handling & Fallbacks
- If local LLM fails schema validation, retry with constrained temperature (0.1) up to 2 times.
- If inference fails, fall back to a cached pre-spec workout stored on disk.
