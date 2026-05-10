# Run History and API Budget

This document records the complete run sequence for the experimental campaign, including
failures, their causes, and the patches applied to fix them. It serves as an audit trail
for anyone checking the database state or the budget accounting.

---

## Database state

| File | Description |
|---|---|
| `data/mirage_strategic.db` | **The analysis database.** 170 games, 1700 rounds, 68 observations, 17 matches, 316 attribution_scores rows. |
| `data/mirage_strategic.db.bak` | Backup of the first completed run, generated under the earlier cooperative-baseline agent prompt. Excluded from analysis (different prompt regime). |
| `data/mirage_strategic.db.bak2` | Backup of the second failed run, which aborted with a schema INSERT error after ~4 LLM games. No usable data. |
| `data/mirage.db` | Earlier experimental database from before the current campaign. |
| `data/mirage_clean_coopbaseline.db` | Earlier database from the cooperative-baseline prompt regime. |
| `data/mirage_contaminated.db` | Earlier database containing API-error-contaminated runs. |

---

## Step-by-step run log

| Step | Script | Status | API calls (est.) | Cumulative | Notes |
|---|---|---|---:|---:|---|
| STEP 0 | Import verification | PASS | 0 | 0 | transforms ok, persuasion ok, database ok |
| STEP 0 | Schema migration | PASS | 0 | 0 | spec_name column added, attribution_scores table created |
| DB RESET 1 | mv to .bak | DONE | 0 | 0 | Prior run under different prompt regime excluded |
| STEP 1 | test_transforms.py | PASS | 0 | 0 | All 7 original tests passed; no API calls |
| STEP 2 | quick_test.py | PASS | 12 | 12 | LLM game (10 calls) + observer (2 calls); all valid |
| STEP 3 (attempt 1) | run_experiment.py | FAIL | ~80 | ~92 | OperationalError: games table had 14 columns, INSERT passed 14 values but schema now had 15 (spec_name added). Four in-flight LLM games completed before crash. |
| FIX | database.py save_transcript | APPLIED | 0 | ~92 | Changed positional INSERT to named-column INSERT. Grepped for other positional INSERTs into games: none found. |
| DB RESET 2 | mv to .bak2 | DONE | 0 | ~92 | 4 contaminated LLM game rows discarded. |
| STEP 3 (retry) | run_experiment.py | PASS | 468 | ~560 | 20 LLM games, 60 scripted games, 17 matched pairs, 68 observer calls. |
| STEP 4 (attempt 1) | run_ablation.py | FAIL (silent) | 0 | ~560 | All 136 attribution_scores rows had api_error=1. Root cause: run_ablation.py lacked dotenv bootstrap; Anthropic client had no API key; SDK rejected every call client-side before HTTP. Zero real API calls made. |
| FIX | run_ablation.py + run_persuasion.py | APPLIED | 0 | ~560 | Added load_dotenv() + ANTHROPIC_API_KEY check + explicit api_key= to Anthropic() constructor in both scripts. Same pattern as run_experiment.py. |
| DB WIPE | attribution_scores only | DONE | 0 | ~560 | DELETE FROM attribution_scores. games/rounds/observations/matches untouched. |
| STEP 4 (retry) | run_ablation.py | PASS | 476 | ~1036 | 340 wrap_rationale calls (Haiku) + 136 observer calls. 0 api_errors. |
| STEP 5 (attempt 1) | run_persuasion.py | FAIL | ~440 | ~1476 | ImportError: cannot import name 'AgentTurn' from 'src.game'. Crashed on first scripted_wrapped call after all_cooperate persuader (200 calls) and vanilla_baseline (200 calls) completed. ~40 observer calls also made before crash. |
| FIX | run_persuasion.py _make_bare_scripted_transcript | APPLIED | 0 | ~1476 | Replaced AgentTurn import with Turn from src.agents; corrected GameTranscript constructor to match actual signature. Same fix as Patch 1 on persuasion.py. |
| DB WIPE | persuasion rows only | DONE | 0 | ~1476 | DELETE FROM attribution_scores WHERE condition IN ('persuader','vanilla_baseline','scripted_wrapped'); corresponding games/rounds deleted. attribution_scores: 136, games: 80. |
| STEP 5 (retry) | run_persuasion.py | PASS | 1980 | ~3456 | 90 transcripts (3 specs × 3 conditions × 10), 180 observer calls. 0 api_errors. |
| STEP 6 | run_within_llm_ablation.py | PASS | 408 | ~3864 | 340 Sonnet calls (neutral_rewrite) + 68 Haiku observer calls. 0 api_errors. |
| SANITY | Sonnet model check | PASS | 1 | ~3865 | claude-sonnet-4-20250514 callable; deprecation warning noted (EOL June 2026). |
| SPOT-CHECK | neutral_rewrite display | N/A | 20 | ~3885 | Re-ran wrap on one transcript for human inspection only; not part of analysis dataset. |

---

## Errors and root causes

**Error 1: OperationalError on games INSERT**

The schema migration in `init_db` added a `spec_name` column (column 15) to the `games` table.
The existing `save_transcript` function used a positional `INSERT OR REPLACE INTO games VALUES
(?, ..., ?)` with 14 placeholders. SQLite rejected this. Fix: change to a named-column INSERT
that explicitly lists the 14 original columns, leaving `spec_name` as NULL (to be set later
by `insert_transcript`).

**Error 2: Silent api_error on all attribution_scores rows (auth failure)**

`run_ablation.py` and `run_persuasion.py` called `Anthropic()` without loading `.env` or
passing `api_key=`. `run_experiment.py` had always called `load_dotenv()` before constructing
the client; the new scripts did not. The SDK rejects authentication-less calls client-side,
before any HTTP request, so zero actual API calls were made. The observer's fallback path
returned neutral scores with `api_error=True` for every row. Fix: add the same dotenv bootstrap
to both scripts.

**Error 3: ImportError in run_persuasion.py**

`_make_bare_scripted_transcript` imported `AgentTurn` from `src.game`. That class does not
exist; the actual per-turn dataclass is `Turn` in `src.agents`. The same issue had been
patched in `src/persuasion.py` (Patch 1) but `scripts/run_persuasion.py` was not modified at
the same time to avoid modifying new files preemptively. Fix: replace the import and
constructor call, same as Patch 1.

---

## Budget summary

| Category | Calls |
|---|---:|
| quick_test (STEP 2) | ~12 |
| run_experiment (STEP 3 retry) | ~468 |
| Failed STEP 3 attempt (sunk, before crash) | ~80 |
| run_ablation (STEP 4 retry) | ~476 |
| Failed STEP 4 attempt (auth failure; zero real calls) | 0 |
| run_persuasion (STEP 5 retry) | ~1980 |
| Failed STEP 5 attempt (partial; before crash) | ~440 |
| run_within_llm_ablation (STEP 6) | ~408 |
| Miscellaneous (sanity check, spot-check display) | ~21 |
| **Total** | **~3,885** |

The 4,000-call cap established at project start was not exceeded. Approximately 520 calls were
wasted on failed or aborted runs and are not reflected in the analysis dataset.
