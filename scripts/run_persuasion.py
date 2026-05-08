"""Persuasion pilot: hold action sequence fixed, vary surface text aggression.

Usage:
    python -m scripts.run_persuasion

This script implements the pilot for the professor's point 3. For each
fixed action spec in CANONICAL_SPECS, it generates three classes of
transcript at the same alpha*:

  1. Persuader: LLM prompted to maximize apparent agency / reflectivity.
  2. Vanilla baseline: LLM playing the same alpha* with neutral prompting.
  3. Scripted-wrapped: a synthetic transcript where the actions come from
     spec and the rationale is generated post-hoc by wrap_rationale.

All three are scored by the judge. The contrast that addresses the
professor's question is `persuader minus vanilla baseline` at fixed
alpha*: if persuader transcripts get higher scores, the judge can be
manipulated by surface-feature engineering.

This is a pilot. We default to N_PER_CONDITION = 10 transcripts per
spec per condition. Bump this up if API budget and time allow.
"""
from __future__ import annotations

import os
import uuid

from anthropic import Anthropic
from dotenv import load_dotenv

from config import (
    AGENT_MODEL,
    DATABASE_PATH,
    OBSERVER_MODEL,
    PAYOFFS,
)
from src.observer import MindAttributionObserver
from src.persuasion import (
    CANONICAL_SPECS,
    FixedActionSpec,
    generate_persuader_transcript,
    generate_vanilla_baseline_transcript,
)
from src.transforms import wrap_rationale


# ---------------------------------------------------------------------------
# Pilot parameters
# ---------------------------------------------------------------------------

N_PER_CONDITION: int = 10  # transcripts per (spec, condition)

COND_PERSUADER = "persuader"
COND_VANILLA = "vanilla_baseline"
COND_SCRIPTED_WRAPPED = "scripted_wrapped"

ALL_CONDITIONS = (COND_PERSUADER, COND_VANILLA, COND_SCRIPTED_WRAPPED)


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

    for spec in CANONICAL_SPECS:
        print(f"\n=== spec: {spec.name} ===")
        _run_one_spec(spec=spec, client=client, observer=observer)

    print("\npersuasion pilot complete")


def _run_one_spec(
    spec: FixedActionSpec,
    client: Anthropic,
    observer: MindAttributionObserver,
) -> None:
    # Persuader transcripts
    print(f"  generating {N_PER_CONDITION} persuader transcripts...")
    for i in range(N_PER_CONDITION):
        tid = f"persuader__{spec.name}__{i:02d}__{_short_uid()}"
        transcript = generate_persuader_transcript(
            spec=spec,
            transcript_id=tid,
            client=client,
            payoffs=PAYOFFS,
        )
        _persist_transcript(transcript, condition=COND_PERSUADER, spec_name=spec.name)
        _score_and_persist(transcript, COND_PERSUADER, spec.name, observer)

    # Vanilla baseline
    print(f"  generating {N_PER_CONDITION} vanilla-baseline transcripts...")
    for i in range(N_PER_CONDITION):
        tid = f"vanilla__{spec.name}__{i:02d}__{_short_uid()}"
        transcript = generate_vanilla_baseline_transcript(
            spec=spec,
            transcript_id=tid,
            client=client,
            payoffs=PAYOFFS,
        )
        _persist_transcript(transcript, condition=COND_VANILLA, spec_name=spec.name)
        _score_and_persist(transcript, COND_VANILLA, spec.name, observer)

    # Scripted-wrapped: build a scripted-style transcript from the spec
    # then wrap rationale via the same path as the ablation.
    print(f"  generating {N_PER_CONDITION} scripted-wrapped transcripts...")
    for i in range(N_PER_CONDITION):
        tid = f"scriptedwrap__{spec.name}__{i:02d}__{_short_uid()}"
        bare = _make_bare_scripted_transcript(spec, transcript_id=tid)
        wrapped = wrap_rationale(bare, client=client, model=AGENT_MODEL)
        _persist_transcript(wrapped, condition=COND_SCRIPTED_WRAPPED, spec_name=spec.name)
        _score_and_persist(wrapped, COND_SCRIPTED_WRAPPED, spec.name, observer)


def _score_and_persist(
    transcript,
    condition: str,
    spec_name: str,
    observer: MindAttributionObserver,
) -> None:
    score_a = observer.score_agent(transcript, target="A")
    score_b = observer.score_agent(transcript, target="B")
    _persist_score(score_a, condition=condition, spec_name=spec_name)  # DB:
    _persist_score(score_b, condition=condition, spec_name=spec_name)  # DB:


# ---------------------------------------------------------------------------
# Utility: build a bare scripted transcript from a fixed action spec
# ---------------------------------------------------------------------------

def _make_bare_scripted_transcript(spec: FixedActionSpec, transcript_id: str):
    """Construct a scripted-format transcript with no rationale text.

    Same shape as what scripted agents in src/agents.py produce. Used as
    the input to wrap_rationale in the scripted-wrapped condition.
    """
    from src.game import GameTranscript, Round
    from src.agents import Turn

    cum_a = 0
    cum_b = 0
    rounds = []
    for t, (a, b) in enumerate(zip(spec.actions_a, spec.actions_b), start=1):
        pa, pb = PAYOFFS[(a, b)]
        cum_a += pa
        cum_b += pb
        rounds.append(
            Round(
                round_num=t,
                agent_a_turn=Turn(action=a, rationale=""),
                agent_b_turn=Turn(action=b, rationale=""),
                payoff_a=pa,
                payoff_b=pb,
            )
        )

    return GameTranscript(
        game_id=transcript_id,
        agent_a_id=f"{transcript_id}_A",
        agent_a_class="scripted",
        agent_a_name=f"persuasion_spec_{spec.name}",
        agent_b_id=f"{transcript_id}_B",
        agent_b_class="scripted",
        agent_b_name=f"persuasion_spec_{spec.name}",
        rounds=rounds,
    )


def _short_uid() -> str:
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Database integration stubs
# ---------------------------------------------------------------------------

def _persist_transcript(transcript, condition: str, spec_name: str) -> None:
    """DB: insert the transcript with a condition tag and spec name.

    Suggested schema additions to your existing transcripts table:
        condition TEXT,
        spec_name TEXT,
        is_persuasion BOOLEAN DEFAULT 0
    """
    from src.database import insert_transcript  # adapt to your API
    insert_transcript(
        transcript,
        condition=condition,
        spec_name=spec_name,
        db_path=DATABASE_PATH,
    )


def _persist_score(score, condition: str, spec_name: str) -> None:
    """DB: insert the attribution score with condition + spec_name tags."""
    from src.database import insert_attribution_score  # adapt to your API
    insert_attribution_score(
        score,
        condition=condition,
        spec_name=spec_name,
        db_path=DATABASE_PATH,
    )


if __name__ == "__main__":
    main()
