# Project Goal

Build an adaptive running coach using COROS data and an auditable training engine. The system
must separate external data, deterministic physiological decisions, and LLM-assisted
interpretation.

## Architectural Rules

- COROS MCP is read-only in the current phase.
- Never implement write-back to COROS unless explicitly requested in a future sprint.
- COROS response schemas must not leak into the core domain.
- All COROS data must pass through an adapter or mapper layer.
- Domain models must remain independent from external providers.
- Deterministic engines own physiological and safety decisions.
- LLMs may interpret, explain, summarize and choose only among allowed actions.
- An LLM must never invent arbitrary pace targets, load limits or recovery thresholds.
- Missing data must be explicit and must not be silently fabricated.
- All important decisions must be testable and auditable.
- Prefer small modules and pure functions for training calculations.
- Do not introduce frameworks unless the current sprint requires them.
- Avoid premature abstraction.
- Avoid premature persistence.
- Avoid multi-agent frameworks unless explicitly requested.

## Data Analysis Rules

- Do not conclude from aggregate activity averages when detailed activity data is available.
- For suspicious heart-rate, pace or execution patterns, inspect activity detail.
- Use lap data when workout structure matters.
- Use custom time windows or FIT data when lap data is insufficient.
- Distinguish evidence from hypothesis.
- Never state that a pattern is caused by fatigue, cardiac drift, heat, terrain or sprints
  without sufficient supporting data.

## Training Safety Rules

- Never compensate missed sessions by automatically stacking load into later days.
- Safety rules override performance optimization.
- Pain or medical warning signals must not be interpreted as ordinary fatigue.
- The system is not a medical diagnosis tool.
- Adaptations must be explainable.
- Progressive overload must be controlled and based on recent context.

## Code Quality Rules

- Use Python 3.12.
- Type hints are required for public functions.
- Use Pydantic for boundary and domain data models when appropriate.
- Use pytest for tests.
- Use Ruff for linting and formatting checks.
- Use mypy for static type checking.
- Keep functions focused.
- Prefer dependency injection over hidden globals.
- Do not place business logic inside API routes.
- Do not make direct MCP calls from domain or engine modules.
- Do not make direct LLM calls from deterministic engine modules.

## Testing Rules

- Every engine rule added in future sprints must have tests.
- Real athlete scenarios may be represented as sanitized fixtures.
- Tests must distinguish input data, expected classification and reasoning metadata.
- Avoid tests that depend on live COROS access unless explicitly marked as integration tests.

## Current Sprint

Only Sprint 5 — Adaptation Engine is currently in scope. COROS remains read-only. Do not implement
safety engines, persistence, API endpoints, LLM integration, or write-back prematurely.
