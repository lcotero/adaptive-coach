# Adaptive Coach — Development Plan

## Purpose

This document is the execution guide for the development of `adaptive-coach`.

It complements `AGENTS.md`:

- `AGENTS.md` defines permanent architectural, safety, data-analysis and code-quality rules.
- `DEVELOPMENT_PLAN.md` defines the delivery sequence, sprint boundaries and implementation goals.

Agents working in this repository must read both files before making changes.

---

# Product Goal

Build a read-only adaptive running coach that:

1. reads athlete and training data from COROS through MCP;
2. normalizes external data into provider-independent internal domain models;
3. analyzes training execution using deterministic and testable engines;
4. evaluates readiness and longer-term athlete state;
5. produces allowed adaptation options through deterministic logic;
6. applies safety rules before any recommendation is surfaced;
7. uses an LLM only to interpret context, explain decisions, summarize findings, and choose among explicitly allowed actions;
8. operates initially as a Shadow Coach without modifying COROS workouts or calendars.

The project must remain explainable, auditable and conservative.

---

# Core Architecture

```text
COROS MCP
    |
    v
Coros Adapter
    |
    v
Internal Domain Models
    |
    +----------------------+
    |                      |
    v                      v
Activity Analysis      Athlete State
Engine                 Engine
    |                      |
    +----------+-----------+
               |
               v
        Adaptation Engine
               |
               v
          Safety Engine
               |
               v
           LLM Coach
               |
               v
          Shadow Coach
```

---

# Development Principles

1. Implement one sprint at a time.
2. Do not implement future sprint functionality prematurely.
3. Keep external provider schemas out of the domain layer.
4. Prefer deterministic logic for physiological and safety decisions.
5. Use LLMs only where language interpretation or contextual explanation adds value.
6. Every engine rule must be testable.
7. Missing data must remain explicit.
8. Do not infer causes from aggregate metrics when detailed activity data is available.
9. When workout structure matters, inspect laps, custom segments or FIT data.
10. Distinguish evidence, hypothesis and recommendation.
11. COROS remains read-only until a future sprint explicitly changes that decision.
12. Avoid frameworks and infrastructure until the sprint actually needs them.

---

# Sprint Roadmap

## Sprint 0 — Project Foundation

Status: COMPLETE

Deliverables:

- Python 3.12 project foundation.
- Modular package structure.
- `pyproject.toml`.
- Ruff, mypy and pytest configuration.
- `README.md`.
- `AGENTS.md`.
- `Makefile`.
- Import smoke test.

No business logic.

---

## Sprint 1 — Internal Domain Models

Status: COMPLETE

Goal:

Create a clean, provider-independent internal domain.

Deliverables:

- enums for sport type, session type, intensity type and subjective state;
- `Activity`;
- `ActivityLap`;
- `TrainingLoadState`;
- `RecoveryState`;
- `RunningFitnessState`;
- `SubjectiveFeedback`;
- `PlannedWorkout`;
- `AthleteSnapshot`;
- validation tests;
- serialization tests where useful.

No COROS adapter.
No MCP calls.
No engines.
No API routes.
No persistence.
No LLM integration.

Detailed Sprint 1 implementation instructions are defined later in this document.

---

## Sprint 2 — COROS Adapter Contract

Status: COMPLETE

Goal:

Introduce a provider boundary without coupling the domain to COROS response schemas.

Deliverables:

- adapter interfaces or protocols;
- mapper functions from COROS-shaped input DTOs to domain models;
- explicit missing-data handling;
- integration boundary tests with sanitized fixture payloads;
- no live COROS dependency in unit tests.

The adapter must support future capabilities for:

- recent activity list;
- activity detail;
- lap data;
- custom segment data;
- FIT access;
- training load;
- training schedule;
- recovery and fitness metrics when available.

No engine logic.

---

## Sprint 3 — Activity Analysis Engine

Status: COMPLETE

Goal:

Convert completed sessions into structured execution analysis.

Initial deliverables:

- session classification support;
- pace stability;
- heart-rate response;
- cardiac drift calculation only where methodologically valid;
- interval consistency;
- pace decay;
- planned vs actual comparison;
- execution score;
- structured evidence and reasoning metadata.

The engine must never attribute causes such as fatigue, heat, terrain or sprint effects without supporting evidence.

Real athlete scenarios may be used as sanitized fixtures.

---

## Sprint 4 — Athlete State Engine

Status: COMPLETE

Goal:

Separate short-term readiness from longer-term training state.

Initial deliverables:

### Readiness state

- GREEN
- YELLOW
- ORANGE
- RED

### Training state

- RECOVERED
- NORMAL
- ACCUMULATING_FATIGUE
- FATIGUED
- OVERREACHED
- RETURNING
- TAPERING
- RACE_READY

Inputs may include:

- recent load;
- load ratio;
- recovery;
- HRV and baseline deviation;
- resting heart rate;
- sleep;
- recent execution quality;
- subjective feedback;
- recent training consistency.

Weights and thresholds must be explicit, versioned and testable.

---

## Sprint 5 — Adaptation Engine

Goal:

Generate safe, explicit, allowed adaptation actions.

Initial actions may include:

- KEEP;
- REDUCE_VOLUME;
- REDUCE_REPETITIONS;
- REDUCE_INTENSITY;
- REPLACE_WITH_EASY;
- RECOVERY_ONLY;
- REST.

The engine must:

- never stack missed workload automatically;
- never invent new load to compensate for missed sessions;
- preserve phase and objective context;
- produce reasons and evidence references.

No LLM decision freedom outside allowed actions.

---

## Sprint 6 — Safety Engine

Goal:

Create a final deterministic authority over recommendations.

Responsibilities:

- block unsafe intensity;
- detect pain or medical warning signals;
- apply conservative overrides;
- flag insufficient data;
- downgrade recommendation confidence when evidence is incomplete;
- prevent optimization rules from overriding safety.

The Safety Engine must run before recommendations reach the user.

---

## Sprint 7 — Shadow Coach

Goal:

Produce read-only adaptive recommendations and compare them with actual athlete behavior.

Flow:

```text
planned workout
      +
athlete snapshot
      +
recent activity analysis
      +
macrocycle context
      |
      v
allowed actions
      |
      v
safety validation
      |
      v
shadow recommendation
      |
      v
actual athlete execution
      |
      v
retrospective comparison
```

The output should include:

- recommended action;
- confidence;
- evidence;
- assumptions;
- uncertainty;
- abort conditions where relevant;
- retrospective outcome when later data becomes available.

---

## Sprint 8 — LLM Coach Layer

Goal:

Add contextual interpretation and explanation without giving the LLM physiological authority.

The LLM may:

- summarize;
- explain;
- contextualize;
- compare options;
- choose among allowed actions;
- generate natural-language coaching feedback.

The LLM may not:

- invent pace targets;
- invent thresholds;
- create actions outside the allowed action set;
- override safety rules;
- fabricate missing metrics.

Provider abstraction should be introduced only at this sprint.

---

## Sprint 9 — API Layer

Goal:

Expose stable application use cases through FastAPI.

Potential endpoints:

- athlete snapshot;
- recent activity analysis;
- readiness;
- training state;
- shadow recommendation;
- feedback submission.

No business logic inside routes.

---

## Sprint 10 — Persistence and Audit Trail

Goal:

Store snapshots, analyses and decisions for longitudinal comparison.

Potential entities:

- athlete snapshots;
- normalized activities;
- activity analyses;
- subjective feedback;
- adaptation decisions;
- safety decisions;
- shadow coach recommendations.

Persistence choice must be justified at that time.

---

## Sprint 11 — Historical Validation

Goal:

Run the system retrospectively on multiple weeks of real training data.

Questions to answer:

- Would the engine have reacted too aggressively?
- Would it have been too conservative?
- Did it identify meaningful deterioration before poor sessions?
- Did it misclassify sprint sessions as cardiac drift?
- Did it account correctly for workout structure?
- Did it preserve key sessions appropriately?
- Were recommendations explainable after seeing the outcome?

---

# Sprint 1 — Detailed Implementation Instructions

## Context and Role

Act as a Staff Software Engineer specialized in Python, domain modeling, typed systems and testable architectures.

You are working in the `adaptive-coach` repository.

Before changing any file:

1. read `AGENTS.md`;
2. read `README.md`;
3. read this `DEVELOPMENT_PLAN.md`;
4. inspect the current repository structure;
5. respect the current sprint boundary.

Implement Sprint 1 only.

---

## Task

Create the provider-independent internal domain models required by future sprints.

Do not connect to COROS.
Do not call MCP.
Do not implement training analysis.
Do not implement readiness calculations.
Do not create API routes.
Do not create persistence.
Do not add LLM dependencies.

---

## Required Structure

Create or update the domain package so it contains:

```text
app/domain/
├── __init__.py
├── activity.py
├── athlete.py
├── enums.py
├── feedback.py
├── load.py
├── recovery.py
├── fitness.py
└── workout.py
```

Tests:

```text
tests/domain/
├── __init__.py
├── test_activity.py
├── test_athlete.py
├── test_feedback.py
├── test_load.py
├── test_recovery.py
└── test_workout.py
```

Keep modules focused and avoid circular imports.

---

## Enums

Create strongly typed enums for at least:

### SportType

Values:

- RUNNING
- TRAIL_RUNNING
- TRACK_RUNNING
- TREADMILL_RUNNING
- STRENGTH
- WALKING
- CYCLING
- SWIMMING
- OTHER

### SessionType

Values:

- EASY
- RECOVERY
- LONG_RUN
- TEMPO
- THRESHOLD
- INTERVAL
- HILLS
- STRIDES
- RACE
- STRENGTH
- CROSS_TRAINING
- OTHER
- UNKNOWN

### IntensityTargetType

Values:

- PACE
- HEART_RATE
- POWER
- RPE
- OPEN

### SubjectiveFeeling

Values:

- VERY_GOOD
- GOOD
- NORMAL
- TIRED
- VERY_TIRED
- POOR

Use string enums.

Do not map COROS numeric sport codes here.

---

## ActivityLap

Create an immutable or effectively immutable Pydantic model representing a normalized lap or segment.

Suggested fields:

- index: int
- distance_m: float | None
- duration_s: float
- avg_pace_s_per_km: float | None
- avg_hr_bpm: int | None
- max_hr_bpm: int | None
- avg_cadence_spm: float | None
- avg_power_w: float | None
- elevation_gain_m: float | None
- elevation_loss_m: float | None

Validation requirements:

- index >= 1
- duration_s > 0
- distance_m >= 0 when present
- heart-rate values > 0 when present
- cadence >= 0 when present
- elevation values >= 0 when present

Do not add COROS-specific IDs.

---

## Activity

Create a normalized completed-activity model.

Suggested fields:

- id: str
- started_at: datetime
- sport_type: SportType
- session_type: SessionType
- title: str | None
- duration_s: float
- distance_m: float | None
- avg_pace_s_per_km: float | None
- avg_hr_bpm: int | None
- max_hr_bpm: int | None
- avg_cadence_spm: float | None
- elevation_gain_m: float | None
- elevation_loss_m: float | None
- training_load: float | None
- aerobic_training_effect: float | None
- anaerobic_training_effect: float | None
- perceived_effort: int | None
- laps: tuple[ActivityLap, ...]

Validation:

- duration_s > 0
- distance_m >= 0 when present
- perceived_effort must use an explicit scale and be validated
- training effect values >= 0 when present

The internal `id` is provider-neutral. It must not be called `labelId`.

---

## TrainingLoadState

Create a model for current training-load context.

Suggested fields:

- short_term_load: float | None
- long_term_load: float | None
- load_ratio: float | None
- observed_at: datetime

Do not derive or calculate ratios here.

This is a state model, not an engine.

---

## RecoveryState

Suggested fields:

- recovery_score: float | None
- hrv_ms: float | None
- hrv_baseline_ms: float | None
- resting_hr_bpm: int | None
- sleep_duration_s: float | None
- observed_at: datetime

Validation:

- recovery score must have a documented scale;
- heart rate > 0 when present;
- HRV > 0 when present;
- sleep duration >= 0 when present.

Do not infer readiness here.

---

## RunningFitnessState

Suggested fields:

- vo2max: float | None
- running_level: float | None
- threshold_pace_s_per_km: float | None
- threshold_hr_bpm: int | None
- observed_at: datetime

Validation:

- all numeric physiological values must be positive when present.

Do not implement pace zones in Sprint 1.

---

## SubjectiveFeedback

Suggested fields:

- recorded_at: datetime
- rpe: int | None
- feeling: SubjectiveFeeling | None
- pain_score: int | None
- sleep_quality: int | None
- stress_level: int | None
- notes: str | None

Use documented scales.

Recommended scales:

- RPE: 1–10
- pain_score: 0–10
- sleep_quality: 1–5
- stress_level: 1–5

Do not transform subjective feedback into training decisions here.

---

## PlannedWorkout

Create a simple internal representation of a planned session.

Suggested fields:

- id: str
- scheduled_date: date
- session_type: SessionType
- title: str
- planned_duration_s: float | None
- planned_distance_m: float | None
- intensity_target_type: IntensityTargetType
- target_min: float | None
- target_max: float | None
- notes: str | None

Validation:

- durations and distances >= 0 when present;
- if both target_min and target_max are present, target_min <= target_max.

Do not create interval-step structures yet unless clearly necessary for model coherence. Prefer minimality.

---

## AthleteSnapshot

Create a snapshot model that represents the athlete state at one point in time.

Suggested fields:

- snapshot_at: datetime
- recent_activities: tuple[Activity, ...]
- training_load: TrainingLoadState | None
- recovery: RecoveryState | None
- running_fitness: RunningFitnessState | None
- subjective_feedback: SubjectiveFeedback | None
- planned_workout: PlannedWorkout | None

This model aggregates state only.

Do not calculate readiness.
Do not calculate fatigue.
Do not classify risk.
Do not generate recommendations.

---

## Model Design Rules

- Use Pydantic v2 models.
- Use explicit field descriptions where units or scale are not obvious.
- Prefer tuples over mutable lists for immutable snapshots.
- Prefer timezone-aware datetimes.
- Validate timezone awareness for `datetime` fields.
- Keep missing data explicit with `None`.
- Never invent defaults for missing physiological data.
- Avoid provider-specific terminology.
- Avoid methods that perform business logic.
- Serialization must remain simple and deterministic.

---

## Package Exports

Update `app/domain/__init__.py` so future modules can import domain types from a stable location.

Example intent:

```python
from app.domain import Activity, AthleteSnapshot, SessionType
```

Do not export internal helper functions.

---

## Tests

Add meaningful model validation tests.

At minimum test:

### Activity and ActivityLap

- valid construction;
- invalid negative duration;
- invalid lap index;
- invalid heart-rate values;
- tuple-based laps;
- provider-neutral naming.

### SubjectiveFeedback

- valid boundary values;
- invalid RPE;
- invalid pain score;
- invalid sleep quality;
- invalid stress level.

### PlannedWorkout

- valid targets;
- invalid target range;
- negative duration rejected.

### RecoveryState

- invalid HRV;
- invalid resting HR;
- invalid sleep duration.

### AthleteSnapshot

- accepts missing optional state;
- aggregates valid nested models;
- rejects naive datetimes if timezone-awareness validation is implemented centrally.

Do not write tests that assume COROS payloads.

---

## Code Quality Criteria

The implementation must:

- pass Ruff;
- pass mypy;
- pass pytest;
- avoid circular imports;
- avoid business logic;
- avoid external-provider coupling;
- avoid unnecessary abstractions;
- use clear units in field names;
- contain no placeholders for future services;
- contain no dead code.

---

## Required Final Verification

Before finishing:

1. run `ruff check .`;
2. run `mypy app`;
3. run `pytest`;
4. fix all failures;
5. summarize files created or modified;
6. list any design decisions taken;
7. confirm no Sprint 2 work was implemented.

Do not start Sprint 2.

---

# Agent Workflow for Future Sprints

For each future sprint:

1. Read:
   - `AGENTS.md`
   - `README.md`
   - `DEVELOPMENT_PLAN.md`

2. Inspect:
   - current git diff;
   - existing tests;
   - current package boundaries.

3. Implement only the active sprint.

4. Run:
   - Ruff;
   - mypy;
   - pytest.

5. Stop after the active sprint.

6. Report:
   - files changed;
   - decisions made;
   - validation output;
   - risks or open questions.

---

# Current Active Sprint

Sprint 4 — Athlete State Engine (COMPLETE)

Do not proceed to Sprint 5 without explicit instruction.
