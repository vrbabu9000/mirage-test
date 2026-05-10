# Code Architecture, Pipeline, and Reproducibility

This document describes the repository structure, the pipeline from configuration to results,
the database schema, and the steps required to reproduce a run.

---

## Pipeline overview

```
config.py + .env (API key, model names, payoffs, thresholds)
        │
        ▼
scripts/run_experiment.py
    Phase 1: 20 LLM-vs-LLM games (parallelized, 4 workers)
    Phase 2: 60 scripted games (sequential, no API cost)
    Phase 3: greedy Hamming matching → 17 matched pairs
    Phase 4: observer scores on all matched transcripts
        │
        ├── scripts/run_ablation.py
        │       Loads matched pairs from DB
        │       Applies strip_reasoning (LLM_minus_r, no API) and
        │       wrap_rationale (scripted_plus_r, 20 calls/pair)
        │       Observer scores all four conditions per pair
        │
        ├── scripts/run_within_llm_ablation.py
        │       Applies total_strip (LLM_total_strip, no API) and
        │       neutral_rewrite (LLM_neutral_rewrite, 20 Sonnet calls/pair)
        │       Observer scores both conditions per pair
        │
        └── scripts/run_persuasion.py
                For each of 3 canonical action specs:
                    10 persuader transcripts (20 Haiku calls each)
                    10 vanilla_baseline transcripts (20 Haiku calls each)
                    10 scripted_wrapped transcripts (20 Haiku calls each)
                    Observer scores all 30 transcripts × 2 targets
```

Every write in the pipeline goes to the SQLite database at `data/mirage_strategic.db`.
Scripts do not depend on each other's in-memory state; they communicate only through the DB.
`run_ablation.py`, `run_within_llm_ablation.py`, and `run_persuasion.py` all require a
completed `run_experiment.py` pass.

---

## Models

| Usage | Model |
|---|---|
| LLM agents (game play) | `claude-haiku-4-5-20251001` |
| Observer / judge (all conditions) | `claude-haiku-4-5-20251001` |
| wrap_rationale rewriter | `claude-haiku-4-5-20251001` |
| neutral_rewrite rewriter | `claude-sonnet-4-20250514` |
| Persuader and vanilla_baseline generator | `claude-haiku-4-5-20251001` |

The neutral_rewrite rewriter is intentionally decoupled from the judge model so the
rewriting operation does not share any parameters with the scoring operation.

---

## Module descriptions (`src/`)

**`config.py`** (project root)
All tunable parameters. Payoff matrix, `TOTAL_ROUNDS = 10`, `N_LLM_GAMES = 20`,
`N_SCRIPTED_GAMES = 60`, `HAMMING_THRESHOLD = 4`, `RUBRIC_DIMENSIONS` (tuple of six dimension
names in canonical order), `DATABASE_PATH`, model names, temperature, and token limits.
Edit here first; do not scatter constants across other files.

**`src/agents.py`**
Defines the `Agent` abstract base class and all concrete agent implementations:
`LLMAgent` (Claude Haiku, produces reasoning traces), `TitForTatAgent`, `WinStayLoseShiftAgent`,
`GrimTriggerAgent`, `AllDefectAgent`, and `FixedMixedAgent`. All return a `Turn(action, rationale)`
dataclass. `Action = Literal["C", "D"]`.

**`src/game.py`**
The PD game engine. `play_game(agent_a, agent_b, game_id)` runs one full game and returns
a `GameTranscript` dataclass containing `game_id`, agent metadata, and a list of `Round`
objects. `Round` holds `agent_a_turn`, `agent_b_turn`, `payoff_a`, `payoff_b`. Action sequences
and total payoffs are computed as properties from the rounds list. `compute_external_regret`
computes $R_i^{\text{ext}}$ against the best fixed action in hindsight.

**`src/observer.py`**
The mind-attribution observer. `MindAttributionObserver.score_agent(transcript, target)` makes
one Anthropic tool-use call, enforcing structured JSON output via the `submit_ratings` tool
schema. Returns an `AttributionScores(transcript_id, agent_id, scores, free_text, api_error)`
dataclass. Condition labels are stripped before the transcript is shown to the observer.
The `api_error` flag is set to `True` when all retries fail; downstream analysis must filter
on it.

**`src/matcher.py`**
Implements `joint_hamming(t1, t2)` and `match_transcripts(llm_transcripts, scripted_transcripts, threshold)`.
Returns a list of `MatchedPair(llm_transcript, scripted_transcript, distance)` dataclasses.
Matching is greedy: LLM transcripts are sorted by game_id; each is paired with the nearest
unused scripted transcript within the threshold.

**`src/transforms.py`**
Four transcript transformation functions, each satisfying $\alpha(\tau') = \alpha(\tau)$:

- `strip_reasoning(transcript)` removes sentences containing any entry of `REASONING_MARKERS`.
  Suffix: `__minus_r`.
- `wrap_rationale(transcript, client)` generates LLM rationale for each round and agent,
  conditioned on the action taken. Suffix: `__plus_r`. 20 API calls per 10-round transcript.
- `total_strip(transcript)` sets every rationale to empty string. No API calls.
  Suffix: `__total_strip`.
- `neutral_rewrite(transcript, client, rewriter_model)` rewrites each rationale via one LLM
  call per round per agent into a neutral mechanical register. Suffix: `__neutral_rewrite`.
  20 API calls per 10-round transcript.

All four call `_assert_actions_preserved` at the end; any action-sequence mutation raises
`AssertionError`. Tests in `scripts/test_transforms.py`.

**`src/persuasion.py`**
Defines `FixedActionSpec(name, actions_a, actions_b)` and two generators:
`generate_persuader_transcript` and `generate_vanilla_baseline_transcript`. Both drive an LLM
round-by-round at a fixed action sequence, differing only in the system prompt. The persuader
prompt instructs for maximal agenticity; the vanilla prompt instructs for minimal neutral
description. `CANONICAL_SPECS` defines the three fixed-action specifications used in the pilot.

**`src/analysis.py`**
Statistical functions: `extract_surface_features(transcript, target)`, `benjamini_hochberg`,
`wilcoxon_per_dimension`, `regress_gap_on_features`. The regression uses OLS with HC3 robust
standard errors via `statsmodels` (soft dependency; absent if `statsmodels` is not installed).

**`src/database.py`**
SQLite persistence layer. Five public write functions: `save_transcript`, `save_observation`,
`save_match`, `insert_transcript` (wrapper adding spec_name), `insert_attribution_score`.
Three public read functions: `load_transcripts_by_condition`, `load_matches`,
`load_matched_pairs` (hydrates `MatchedPair` objects). `init_db` creates the schema and
runs the idempotent `ALTER TABLE games ADD COLUMN spec_name TEXT` migration.

**`src/rate_limit.py`**
`RateLimiter` (token-bucket, 40 req/min by default) and `call_with_backoff(func, max_retries,
base_delay, max_delay)`. All API calls in the codebase go through `call_with_backoff`. On
`RateLimitError`, the `retry-after` header is honored when present. On 5xx errors, exponential
backoff with jitter is used. On 4xx (except 429), the error is raised immediately.

---

## Script descriptions (`scripts/`)

**`scripts/quick_test.py`**
Sanity check. One LLM-vs-LLM game (5 rounds), one TFT-vs-TFT game (5 rounds), observer on
both. Does not write to DB. Run before every experiment to confirm API connectivity.

**`scripts/run_experiment.py`**
Main pipeline orchestrator. Calls `init_db()`, generates all games, matches pairs, runs the
original observer pass, and writes everything to DB via `save_transcript`, `save_match`, and
`save_observation`. Reads `ANTHROPIC_API_KEY` via `load_dotenv()` and errors out if absent.

**`scripts/run_ablation.py`**
2x2 ablation. Reads matched pairs from DB via `load_matched_pairs`. For each pair, applies
`strip_reasoning` and `wrap_rationale`, scores all four conditions with the observer, and
writes rows to `attribution_scores` via `insert_attribution_score`. Uses the same dotenv
bootstrap as `run_experiment.py`.

**`scripts/run_within_llm_ablation.py`**
Within-LLM ablation. Reads matched pairs, applies `total_strip` and `neutral_rewrite`,
scores with the observer, writes to `attribution_scores`. The neutral_rewrite step uses
Sonnet as the rewriter model and Haiku as the judge.

**`scripts/run_persuasion.py`**
Persuasion pilot. Iterates over `CANONICAL_SPECS`; for each spec generates 10 transcripts per
condition (persuader, vanilla_baseline, scripted_wrapped), scores each with the observer, and
writes to both `games/rounds` (via `insert_transcript`) and `attribution_scores`.

**`scripts/test_transforms.py`**
Twelve behavior-preservation tests for all four transforms. Run without API calls by using
`MagicMock` for LLM-dependent transforms. Invoke via `python -m scripts.test_transforms`.
All twelve must pass before running any ablation.

**`scripts/analyze_results.py`**, **`scripts/analyze_filtered.py`**
Post-hoc analysis and statistics printing. Read from DB; no writes. Useful for exploring
results after data collection is complete.

---

## Database schema

The database lives at `data/mirage_strategic.db`. Five tables:

### `games`

One row per game. Populated by `run_experiment.py` (via `save_transcript`) and
`run_persuasion.py` (via `insert_transcript`).

| Column | Type | Notes |
|---|---|---|
| game_id | TEXT PK | Unique game identifier |
| agent_a_id | TEXT | |
| agent_a_class | TEXT | `"llm"` or `"scripted"` |
| agent_a_name | TEXT | Model name or strategy name |
| agent_b_id | TEXT | |
| agent_b_class | TEXT | |
| agent_b_name | TEXT | |
| condition | TEXT | `"llm"`, `"scripted"`, `"persuader"`, `"vanilla_baseline"`, `"scripted_wrapped"` |
| created_at | TEXT | ISO timestamp |
| total_rounds | INTEGER | |
| total_payoff_a | INTEGER | |
| total_payoff_b | INTEGER | |
| cooperation_rate_a | REAL | |
| cooperation_rate_b | REAL | |
| spec_name | TEXT | Null for standard games; set for persuasion pilot rows |

The `spec_name` column was added by schema migration during this campaign. `init_db`
handles existing databases idempotently via a try/except on `ALTER TABLE`.

### `rounds`

One row per round per game. Populated alongside `games`.

| Column | Type | Notes |
|---|---|---|
| game_id | TEXT | FK to games |
| round_num | INTEGER | 1-indexed |
| action_a | TEXT | `"C"` or `"D"` |
| action_b | TEXT | `"C"` or `"D"` |
| rationale_a | TEXT | May be empty string for scripted agents |
| rationale_b | TEXT | |
| payoff_a | INTEGER | |
| payoff_b | INTEGER | |

### `observations`

One row per (game, target agent). Populated by `run_experiment.py` via `save_observation`.
This table holds the original observer pass on matched pairs from `run_experiment`.

| Column | Type | Notes |
|---|---|---|
| game_id | TEXT | |
| target | TEXT | `"A"` or `"B"` |
| scores_json | TEXT | JSON dict: dimension → integer score |
| justification | TEXT | Observer's free-text explanation |
| created_at | TEXT | |

### `matches`

One row per matched pair. Populated by `run_experiment.py`.

| Column | Type |
|---|---|
| llm_game_id | TEXT PK part |
| scripted_game_id | TEXT PK part |
| distance | INTEGER |

### `attribution_scores`

One row per (transcript, target, condition). Populated by the ablation and persuasion
scripts via `insert_attribution_score`. This table is the primary analysis dataset for
all conditions except the original BI violation (which uses `observations`).

| Column | Type | Notes |
|---|---|---|
| transcript_id | TEXT | May include suffixes like `__minus_r`, `__plus_r`, etc. |
| target | TEXT | `"A"` or `"B"` |
| condition | TEXT | One of the six analysis conditions or the three persuasion conditions |
| spec_name | TEXT | Null except for persuasion rows |
| scores_json | TEXT | JSON dict |
| justification | TEXT | |
| api_error | INTEGER | 0 or 1; filter out rows where api_error = 1 before analysis |
| created_at | TEXT | |

Primary key is `(transcript_id, target, condition)`, so re-running a script overwrites prior
results for the same (transcript, condition) cell rather than duplicating rows.

---

## Reproducibility

### Prerequisites

```
Python 3.10+
pip install -r requirements.txt
ANTHROPIC_API_KEY in .env or environment
```

### Run order

Scripts must be run in this order; each step depends on the previous:

```
1. python -m scripts.quick_test         # verify connectivity; ~12 calls
2. python -m scripts.run_experiment     # ~468 calls; ~30 min
3. python -m scripts.run_ablation       # ~476 calls; ~25 min
4. python -m scripts.run_within_llm_ablation  # ~408 calls; ~20 min
5. python -m scripts.run_persuasion     # ~1980 calls; ~90 min
```

Total: approximately 3,350 API calls on `claude-haiku-4-5-20251001` plus approximately 340
calls on `claude-sonnet-4-20250514` (for neutral_rewrite). Estimated cost is under $20 at
current API pricing.

### DB reset

To start a completely fresh run:

```bash
mv data/mirage_strategic.db data/mirage_strategic.db.bak
# init_db() runs automatically at the start of run_experiment.py
```

### Transform invariance tests

Run before any ablation step:

```bash
python -m scripts.test_transforms
```

All twelve tests should pass. These tests use mock LLM clients and make no API calls.

### Current data state

The `data/` directory contains:

- `mirage_strategic.db`: the analysis dataset from the completed experimental campaign.
- `mirage_strategic.db.bak`: the backup from before the first reset (earlier prompt regime).
- `mirage_strategic.db.bak2`: the backup from the second reset (failed INSERT due to schema
  mismatch on the initial retry).
- `mirage.db`, `mirage_clean_coopbaseline.db`, `mirage_contaminated.db`: earlier experimental
  databases from before the current campaign. Not used in the final analysis.

The `data/` directory is gitignored. To share the analysis dataset, either commit the DB
explicitly or export the relevant tables to CSV.
