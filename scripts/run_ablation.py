"""Run the 2x2 ablation: condition (LLM vs scripted) x reasoning (+r vs -r).

Usage:
    python -m scripts.run_ablation

Prerequisites:
    - The original matched-pair experiment has already been run, so
      LLM transcripts and scripted transcripts exist in the database.
    - The matcher has produced MatchedPair records.

This script does NOT regenerate the original LLM or scripted transcripts.
It applies the two transformations (strip_reasoning, wrap_rationale) to
existing matched pairs and re-scores all four resulting transcripts per
matched pair with the judge.

Output: rows in the `attribution_scores` table tagged with one of four
condition labels: 'LLM_plus_r', 'LLM_minus_r', 'scripted_plus_r',
'scripted_minus_r'.

The four-cell judge score table is then ready for analysis in
src/analysis.py (see new function `analyze_2x2_ablation`).

NOTE: this script wires up the database integration with stubs. The
exact INSERT / SELECT calls depend on your src/database.py interface.
Any line marked with `# DB:` is the place where the DB call goes.
Replace stubs with actual calls before running.
"""
from __future__ import annotations

import os

from anthropic import Anthropic
from dotenv import load_dotenv

from config import (
    AGENT_MODEL,
    DATABASE_PATH,
    OBSERVER_MODEL,
)
from src.observer import MindAttributionObserver
from src.transforms import strip_reasoning, wrap_rationale


# ---------------------------------------------------------------------------
# Condition labels (must match what analysis.py and database.py expect)
# ---------------------------------------------------------------------------

COND_LLM_PLUS_R = "LLM_plus_r"
COND_LLM_MINUS_R = "LLM_minus_r"
COND_SCRIPTED_PLUS_R = "scripted_plus_r"
COND_SCRIPTED_MINUS_R = "scripted_minus_r"

ALL_CONDITIONS = (
    COND_LLM_PLUS_R,
    COND_LLM_MINUS_R,
    COND_SCRIPTED_PLUS_R,
    COND_SCRIPTED_MINUS_R,
)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    client = Anthropic(api_key=api_key)
    observer = MindAttributionObserver(client=client, model=OBSERVER_MODEL)

    matched_pairs = _load_matched_pairs()  # DB:
    print(f"loaded {len(matched_pairs)} matched pairs from the original run")

    for i, pair in enumerate(matched_pairs):
        print(f"[{i+1}/{len(matched_pairs)}] processing pair distance={pair.distance}")

        # Cell 1: LLM with reasoning (the original LLM transcript). Already
        # scored by the original observer pass, but we re-score here to
        # keep the comparison apples-to-apples (same observer call site,
        # same temperature).
        _score_and_persist(
            transcript=pair.llm_transcript,
            condition=COND_LLM_PLUS_R,
            observer=observer,
        )

        # Cell 2: LLM with reasoning stripped (cheap, no API calls).
        llm_minus_r = strip_reasoning(pair.llm_transcript)
        _score_and_persist(
            transcript=llm_minus_r,
            condition=COND_LLM_MINUS_R,
            observer=observer,
        )

        # Cell 3: scripted with rationale wrapped (expensive: 2*n API
        # calls for the wrap, plus 2 observer calls).
        scripted_plus_r = wrap_rationale(
            pair.scripted_transcript,
            client=client,
            model=AGENT_MODEL,
        )
        _score_and_persist(
            transcript=scripted_plus_r,
            condition=COND_SCRIPTED_PLUS_R,
            observer=observer,
        )

        # Cell 4: scripted as-is (the original scripted transcript).
        _score_and_persist(
            transcript=pair.scripted_transcript,
            condition=COND_SCRIPTED_MINUS_R,
            observer=observer,
        )

    print("ablation run complete")


def _score_and_persist(
    transcript,
    condition: str,
    observer: MindAttributionObserver,
) -> None:
    """Score both agents in the transcript with the judge and write to DB."""
    score_a = observer.score_agent(transcript, target="A")
    score_b = observer.score_agent(transcript, target="B")
    _persist_score(score_a, condition=condition)  # DB:
    _persist_score(score_b, condition=condition)  # DB:


# ---------------------------------------------------------------------------
# Database integration stubs
# ---------------------------------------------------------------------------

def _load_matched_pairs():
    """DB: read matched pairs created by the original matcher run.

    Returns a list of MatchedPair objects (see src/matcher.py).
    Wire to your existing src/database.py interface.
    """
    from src.database import load_matched_pairs  # adapt to your API
    return load_matched_pairs(DATABASE_PATH)


def _persist_score(score, condition: str) -> None:
    """DB: insert one AttributionScores row tagged with the ablation condition.

    Your existing schema likely already has an `attribution_scores` table.
    Add a `condition` column if it does not exist:

        ALTER TABLE attribution_scores ADD COLUMN condition TEXT;

    Then your insert function should accept the condition as an argument
    and store it alongside the existing fields.
    """
    from src.database import insert_attribution_score  # adapt to your API
    insert_attribution_score(score, condition=condition, db_path=DATABASE_PATH)


if __name__ == "__main__":
    main()
