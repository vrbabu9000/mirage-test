"""Diagnose API rate-limit contamination in the experiment database.

Reads the existing SQLite database and identifies:

1. Rounds where the LLM agent hit a rate limit and defaulted to D.
   Detected by the error sentinel string in the rationale field.

2. Observations where the observer errored out and returned neutral 3s.
   Detected by the error sentinel string in the justification field.

3. Aggregate contamination rates per condition.

4. Games with any contaminated rounds (the candidate games to exclude
   in a filtered re-analysis).

Run:
    python -m scripts.diagnose_rate_limits
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import get_conn


# Sentinel strings that identify error-fallback rows.
AGENT_ERROR_MARKERS = ("API error after retries", "Parse error", "API error", "observer failed")
OBSERVER_ERROR_MARKERS = ("observer failed after", "observer failed")


def is_agent_error(rationale: str) -> bool:
    if not rationale:
        return False
    return any(m in rationale for m in AGENT_ERROR_MARKERS)


def is_observer_error(justification: str) -> bool:
    if not justification:
        return False
    return any(m in justification for m in OBSERVER_ERROR_MARKERS)


def main() -> None:
    with get_conn() as conn:
        # Load all games with their condition.
        game_rows = conn.execute(
            "SELECT game_id, condition FROM games"
        ).fetchall()
        game_condition = {g[0]: g[1] for g in game_rows}

        # Load all rounds.
        round_rows = conn.execute(
            "SELECT game_id, round_num, action_a, action_b, rationale_a, rationale_b FROM rounds"
        ).fetchall()

        # Load all observations.
        obs_rows = conn.execute(
            "SELECT game_id, target, justification FROM observations"
        ).fetchall()

    # Tally agent-side contamination per condition.
    rounds_per_cond: dict[str, int] = defaultdict(int)
    errors_per_cond: dict[str, int] = defaultdict(int)
    contaminated_games: dict[str, set[str]] = defaultdict(set)
    error_details: list[tuple] = []

    for game_id, round_num, action_a, action_b, rat_a, rat_b in round_rows:
        cond = game_condition.get(game_id, "unknown")
        for side, action, rat in (("A", action_a, rat_a), ("B", action_b, rat_b)):
            rounds_per_cond[cond] += 1
            if is_agent_error(rat):
                errors_per_cond[cond] += 1
                contaminated_games[cond].add(game_id)
                error_details.append((game_id, round_num, side, action, rat[:80]))

    # Observer contamination.
    obs_per_cond: dict[str, int] = defaultdict(int)
    obs_errors_per_cond: dict[str, int] = defaultdict(int)
    contaminated_obs: list[tuple] = []
    for game_id, target, justification in obs_rows:
        cond = game_condition.get(game_id, "unknown")
        obs_per_cond[cond] += 1
        if is_observer_error(justification):
            obs_errors_per_cond[cond] += 1
            contaminated_obs.append((game_id, target, justification[:80]))

    # ---- Report ----
    print("=" * 70)
    print(" RATE-LIMIT CONTAMINATION DIAGNOSTIC")
    print("=" * 70)

    print("\nAgent-side contamination (rate-limit fallbacks to D):\n")
    print(f"  {'Condition':<12} {'Turns':>8} {'Errors':>8} {'Rate':>8} {'Games w/err':>14}")
    for cond in sorted(rounds_per_cond):
        total = rounds_per_cond[cond]
        errs = errors_per_cond[cond]
        rate = errs / total if total else 0
        n_bad_games = len(contaminated_games[cond])
        print(f"  {cond:<12} {total:>8d} {errs:>8d} {rate:>8.1%} {n_bad_games:>14d}")

    print("\nObserver-side contamination (observer fallbacks to 3/3/3/...):\n")
    print(f"  {'Condition':<12} {'Obs':>8} {'Errors':>8} {'Rate':>8}")
    for cond in sorted(obs_per_cond):
        total = obs_per_cond[cond]
        errs = obs_errors_per_cond[cond]
        rate = errs / total if total else 0
        print(f"  {cond:<12} {total:>8d} {errs:>8d} {rate:>8.1%}")

    if error_details:
        print(f"\nFirst 10 contaminated agent turns:\n")
        for gid, rn, side, act, rat in error_details[:10]:
            print(f"  {gid}  round {rn}  side {side}  action={act}")
            print(f"    rationale: {rat}...")

    if contaminated_obs:
        print(f"\nFirst 5 contaminated observations:\n")
        for gid, tgt, just in contaminated_obs[:5]:
            print(f"  {gid}  target {tgt}")
            print(f"    justification: {just}...")

    # ---- Recommendation ----
    print("\n" + "=" * 70)
    print(" RECOMMENDATION")
    print("=" * 70)

    total_llm_rounds = rounds_per_cond.get("llm", 0)
    total_llm_errors = errors_per_cond.get("llm", 0)
    n_contaminated_llm_games = len(contaminated_games.get("llm", set()))
    total_llm_games = sum(1 for g, c in game_condition.items() if c == "llm")

    total_obs = sum(obs_per_cond.values())
    total_obs_errors = sum(obs_errors_per_cond.values())

    if total_llm_errors == 0 and total_obs_errors == 0:
        print("\nClean: no detected API-error fallbacks. Current analysis stands.")
    else:
        print(
            f"\n{total_llm_errors} contaminated LLM agent turns in "
            f"{n_contaminated_llm_games}/{total_llm_games} LLM games."
        )
        print(f"{total_obs_errors} contaminated observations out of {total_obs}.")
        print("\nYour options:")
        print("  (A) Re-run the experiment with the new rate-limiter + backoff in place.")
        print("      Reliable and produces a clean dataset.")
        print("  (B) Filter contaminated runs in place and re-run analysis:")
        print("      python -m scripts.analyze_filtered")
        print("      Fast; gives you the 'contamination-robust' numbers for the presentation.")
        print("\nBoth options are defensible. (B) is practical; (A) is gold standard.")


if __name__ == "__main__":
    main()
