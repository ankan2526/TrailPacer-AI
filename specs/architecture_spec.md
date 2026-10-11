# Architecture Specification: TrailPacer AI

## 1. System Overview
TrailPacer AI is architected as an offline-first, spec-driven outdoor workout generator. It uses local open-weight LLMs (e.g., Llama 3.2 3B via Ollama or llama.cpp) to synthesize customized workout regimens strictly bounded by a formal JSON schema.

## 2. Component Architecture

```
[ User / CLI / Client ]
          │
          ▼
   ┌───────────────┐
   │    agent.py   │ ◄─── Prompt harness & local inference runner
   └──────┬────────┘
          │
          ├──────────────────────────┐
          ▼                          ▼
   ┌───────────────┐          ┌──────────────┐
   │ Local LLM API │          │ validator.py │ ◄── Validates against workout_schema.json
   │ (Ollama HTTP) │          └──────┬───────┘
   └──────┬────────┘                 │
          │                          ▼
          │                   [ Pass / Fail ]
          ▼                          │
     Raw Output ─────────────────────┘
          │
     (On Failure: Retry x2 w/ temp=0.1 -> Fallback Cache)
          │
          ▼
   Structured Workout JSON
```

## 3. Specifications & Contracts
- **Schema Contract:** All workout responses must be validated against `specs/workout_schema.json`.
- **Validation Engine:** `src/validator.py` provides pure functional validation and diagnostic reporting.
- **Inference Runtime:** Local HTTP endpoint (`http://localhost:11434/api/generate` by default) running quantized models (`llama3.2:3b` recommended for Apple Silicon / CPU performance targets < 5s).

## 4. Resilience & Fallback Strategy
1. **Primary Generation:** Standard prompt with JSON mode enabled.
2. **Schema Retry Loop:** If raw response fails JSON parsing or JSON Schema validation, retry up to 2 times with a constrained temperature (`0.1`) and error-correcting prompt hints.
3. **Offline Fallback Cache:** If the local inference daemon is unreachable or exhausts retries, serve pre-validated static workouts stored in `specs/fallback_workouts.json` matching the requested activity type.
