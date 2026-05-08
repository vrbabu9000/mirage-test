"""Within-LLM ablation: total_strip and neutral_rewrite at the same matched
pairs from the original run.

Usage:
    python -m scripts.run_within_llm_ablation

For each LLM transcript in the matched pairs created by run_experiment.py:

  Cell A. total_strip       : remove every rationale (set to "");
                              score with the judge.
  Cell B. neutral_rewrite   : rewrite each rationale via Sonnet into a
                              neutral mechanical register that reports
                              only the action; score with the judge.

The rewriter (Sonnet) is intentionally distinct from the agent and
observer model (Haiku) so the strip operation is decoupled from the
judge.

Rows are appended to attribution_scores with conditions
'LLM_total_strip' and 'LLM_neutral_rewrite' (no spec_name).
"""
from __future__ import annotations

import os

from anthropic import Anthropic
from dotenv import load_dotenv

from config import DATABASE_PATH, OBSERVER_MODEL
from src.database import insert_attribution_score, load_matched_pairs
from src.observer import MindAttributionObserver
from src.transforms import neutral_rewrite, total_strip


COND_TOTAL_STRIP = "LLM_total_strip"
COND_NEUTRAL_REWRITE = "LLM_neutral_rewrite"
REWRITER_MODEL = "claude-sonnet-4-20250514"


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    client = Anthropic(api_key=api_key)
    observer = MindAttributionObserver(client=client, model=OBSERVER_MODEL)

    pairs = load_matched_pairs(DATABASE_PATH)
    print(f"loaded {len(pairs)} matched pairs from the original run")

    for i, pair in enumerate(pairs):
        print(f"[{i+1}/{len(pairs)}] processing pair distance={pair.distance}")

        # Cell A: total strip (no generation)
        ts = total_strip(pair.llm_transcript)
        for tgt in ("A", "B"):
            score = observer.score_agent(ts, target=tgt)
            insert_attribution_score(
                score, condition=COND_TOTAL_STRIP, db_path=DATABASE_PATH
            )

        # Cell B: neutral rewrite (Sonnet rewriter, Haiku judge)
        nr = neutral_rewrite(
            pair.llm_transcript,
            client=client,
            rewriter_model=REWRITER_MODEL,
        )
        for tgt in ("A", "B"):
            score = observer.score_agent(nr, target=tgt)
            insert_attribution_score(
                score, condition=COND_NEUTRAL_REWRITE, db_path=DATABASE_PATH
            )

    print("within-LLM ablation complete")


if __name__ == "__main__":
    main()
