"""Quick sanity check: runs one LLM-vs-LLM game and one scripted game,
then scores both. Verifies the API key, models, and full pipeline.

Run with:
    python -m scripts.quick_test
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# Make project root importable when running as `python scripts/quick_test.py` too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anthropic import Anthropic
from dotenv import load_dotenv

from src.agents import LLMAgent, TitForTatAgent
from src.game import compute_external_regret, play_game
from src.observer import MindAttributionObserver


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    client = Anthropic(api_key=api_key)

    print("=== Quick test: one LLM-vs-LLM game ===")
    game_id = f"qtest_llm_{uuid.uuid4().hex[:6]}"
    a = LLMAgent(agent_id=f"{game_id}_A", client=client)
    b = LLMAgent(agent_id=f"{game_id}_B", client=client)

    def on_round(r, _t):
        print(
            f"  R{r.round_num}: A={r.agent_a_turn.action} ({r.agent_a_turn.rationale[:60]}...) "
            f"B={r.agent_b_turn.action}"
        )

    t_llm = play_game(a, b, game_id, total_rounds=5, on_round=on_round)
    print(
        f"  final: A payoff = {t_llm.total_payoff_a}, B payoff = {t_llm.total_payoff_b}, "
        f"coop A = {t_llm.cooperation_rate_a:.2f}, coop B = {t_llm.cooperation_rate_b:.2f}"
    )
    regret_a = compute_external_regret(t_llm.action_sequence_a, t_llm.action_sequence_b)
    print(f"  external regret A: {regret_a['external_regret']}")

    print("\n=== Quick test: one scripted game (TFT vs TFT) ===")
    scr_id = f"qtest_scr_{uuid.uuid4().hex[:6]}"
    t_scr = play_game(
        TitForTatAgent(agent_id=f"{scr_id}_A"),
        TitForTatAgent(agent_id=f"{scr_id}_B"),
        scr_id,
        total_rounds=5,
    )
    print(
        f"  final: A payoff = {t_scr.total_payoff_a}, B payoff = {t_scr.total_payoff_b}"
    )

    print("\n=== Quick test: observer on both games ===")
    observer = MindAttributionObserver(client)
    s_llm = observer.score_agent(t_llm, "A")
    s_scr = observer.score_agent(t_scr, "A")
    print(f"  LLM agent A scores:      {s_llm.scores}")
    print(f"  Scripted agent A scores: {s_scr.scores}")
    print(f"  LLM justification: {s_llm.free_text}")
    print(f"  Scripted justification: {s_scr.free_text}")

    print("\nAll systems go. Ready to run the full experiment.")


if __name__ == "__main__":
    main()
