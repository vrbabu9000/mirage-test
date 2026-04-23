"""Main experimental pipeline.

Runs 20 LLM-vs-LLM games and 60 scripted games with varied strategies,
matches LLM runs to scripted runs by joint Hamming distance, then runs
the mind-attribution observer on every transcript in every matched pair.

Everything is written to SQLite so the Streamlit dashboard can display
results live via auto-refresh.

Run with:
    python -m scripts.run_experiment
"""
from __future__ import annotations

import os
import random
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anthropic import Anthropic
from dotenv import load_dotenv

from config import (
    HAMMING_THRESHOLD,
    MAX_WORKERS,
    N_LLM_GAMES,
    N_SCRIPTED_GAMES,
    TOTAL_ROUNDS,
)
from src.agents import (
    AllDefectAgent,
    FixedMixedAgent,
    GrimTriggerAgent,
    LLMAgent,
    TitForTatAgent,
    WinStayLoseShiftAgent,
)
from src.database import (
    init_db,
    load_transcripts_by_condition,
    save_match,
    save_observation,
    save_transcript,
)
from src.game import play_game
from src.matcher import match_transcripts
from src.observer import MindAttributionObserver


# Factory functions so each game gets fresh agent instances (important for
# stateful strategies like Grim Trigger).
SCRIPTED_FACTORIES = [
    ("tft", lambda i: TitForTatAgent(agent_id=f"tft_{i}")),
    ("wsls", lambda i: WinStayLoseShiftAgent(agent_id=f"wsls_{i}")),
    ("grim", lambda i: GrimTriggerAgent(agent_id=f"grim_{i}")),
    ("alldef", lambda i: AllDefectAgent(agent_id=f"alldef_{i}")),
    (
        "mixed_30",
        lambda i: FixedMixedAgent(
            agent_id=f"mixed30_{i}", p_cooperate=0.3, seed=hash(f"m30_{i}") % 2**31
        ),
    ),
    (
        "mixed_50",
        lambda i: FixedMixedAgent(
            agent_id=f"mixed50_{i}", p_cooperate=0.5, seed=hash(f"m50_{i}") % 2**31
        ),
    ),
    (
        "mixed_70",
        lambda i: FixedMixedAgent(
            agent_id=f"mixed70_{i}", p_cooperate=0.7, seed=hash(f"m70_{i}") % 2**31
        ),
    ),
]


def make_client() -> Anthropic:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    return Anthropic(api_key=api_key)


def run_one_llm_game(client: Anthropic, idx: int):
    game_id = f"llm_{idx:03d}_{uuid.uuid4().hex[:6]}"
    a = LLMAgent(agent_id=f"{game_id}_A", client=client)
    b = LLMAgent(agent_id=f"{game_id}_B", client=client)
    transcript = play_game(a, b, game_id, total_rounds=TOTAL_ROUNDS)
    save_transcript(transcript, condition="llm")
    return transcript


def run_one_scripted_game(idx: int, strat_a, strat_b):
    game_id = f"scr_{idx:03d}_{uuid.uuid4().hex[:6]}"
    a = strat_a[1](idx)
    b = strat_b[1](idx + 10_000)
    transcript = play_game(a, b, game_id, total_rounds=TOTAL_ROUNDS)
    save_transcript(transcript, condition="scripted")
    return transcript


def score_transcript(client: Anthropic, transcript, target: str):
    observer = MindAttributionObserver(client)
    scores = observer.score_agent(transcript, target)
    save_observation(scores)
    return scores


def main() -> None:
    init_db()
    client = make_client()

    # --- Phase 1: LLM games (parallelized) ----------------------------------
    print(f"[1/4] Running {N_LLM_GAMES} LLM-vs-LLM games...")
    llm_transcripts = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(run_one_llm_game, client, i) for i in range(N_LLM_GAMES)]
        for f in as_completed(futures):
            t = f.result()
            llm_transcripts.append(t)
            print(
                f"  LLM game {t.game_id}: "
                f"coop_A={t.cooperation_rate_a:.2f} coop_B={t.cooperation_rate_b:.2f}"
            )

    # --- Phase 2: scripted games (sequential, they're fast) -----------------
    print(f"\n[2/4] Running {N_SCRIPTED_GAMES} scripted games...")
    scripted_transcripts = []
    rng = random.Random(42)
    for i in range(N_SCRIPTED_GAMES):
        strat_a = rng.choice(SCRIPTED_FACTORIES)
        strat_b = rng.choice(SCRIPTED_FACTORIES)
        t = run_one_scripted_game(i, strat_a, strat_b)
        scripted_transcripts.append(t)
        print(
            f"  scripted {t.game_id} ({strat_a[0]} vs {strat_b[0]}): "
            f"coop_A={t.cooperation_rate_a:.2f} coop_B={t.cooperation_rate_b:.2f}"
        )

    # --- Phase 3: matching --------------------------------------------------
    print("\n[3/4] Matching LLM -> scripted by joint Hamming distance...")
    pairs = match_transcripts(
        llm_transcripts, scripted_transcripts, threshold=HAMMING_THRESHOLD
    )
    print(
        f"  Matched {len(pairs)} / {len(llm_transcripts)} LLM games "
        f"at threshold {HAMMING_THRESHOLD}."
    )
    for p in pairs:
        save_match(p.llm_transcript.game_id, p.scripted_transcript.game_id, p.distance)
        print(
            f"    {p.llm_transcript.game_id} <-> {p.scripted_transcript.game_id} "
            f"(joint_hamming = {p.distance})"
        )

    # --- Phase 4: observer (parallelized) -----------------------------------
    print("\n[4/4] Running observer on matched pairs (both agents per game)...")
    jobs = []
    for p in pairs:
        for target in ("A", "B"):
            jobs.append((p.llm_transcript, target))
            jobs.append((p.scripted_transcript, target))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(score_transcript, client, t, target) for t, target in jobs]
        for f in as_completed(futures):
            s = f.result()
            print(f"  scored {s.transcript_id} agent {s.agent_id}: {s.scores}")

    print("\nDone. Run `streamlit run app.py` to view results.")


if __name__ == "__main__":
    main()
