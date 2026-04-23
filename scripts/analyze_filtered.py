"""Filtered re-analysis that excludes rate-limit-contaminated runs.

Strategy:
  1. Identify games with any API-error fallbacks in their rounds.
  2. Identify observations with the observer error sentinel.
  3. Rebuild the matched-pair set using only clean games and clean
     observations.
  4. Re-run Wilcoxon + regression on the clean subset.
  5. Report: original n, contaminated n, clean n, and the key test
     statistics for both samples side-by-side so you can see whether
     the finding is robust to filtering.

Run:
    python -m scripts.analyze_filtered
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config import RUBRIC_DIMENSIONS
from scripts.diagnose_rate_limits import is_agent_error, is_observer_error
from src.analysis import (
    extract_surface_features,
    regress_gap_on_features,
    wilcoxon_per_dimension,
)
from src.database import (
    get_conn,
    load_matches,
    load_observation,
    load_transcripts_by_condition,
)
from src.matcher import MatchedPair


def find_contaminated_games() -> set[str]:
    """Return the set of game_ids that have at least one error-fallback round."""
    bad: set[str] = set()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT game_id, rationale_a, rationale_b FROM rounds"
        ).fetchall()
    for gid, rat_a, rat_b in rows:
        if is_agent_error(rat_a) or is_agent_error(rat_b):
            bad.add(gid)
    return bad


def main() -> None:
    contaminated = find_contaminated_games()
    print(f"Contaminated games (any rate-limit fallback rounds): {len(contaminated)}")

    llm_all = {t.game_id: t for t in load_transcripts_by_condition("llm")}
    scripted_all = {t.game_id: t for t in load_transcripts_by_condition("scripted")}
    matches = load_matches()

    # Full set
    full_pairs: list[tuple] = []
    for llm_gid, scr_gid, dist in matches:
        if llm_gid not in llm_all or scr_gid not in scripted_all:
            continue
        llm_obs = load_observation(llm_gid, "A")
        scr_obs = load_observation(scr_gid, "A")
        if llm_obs is None or scr_obs is None:
            continue
        full_pairs.append((
            MatchedPair(llm_all[llm_gid], scripted_all[scr_gid], dist),
            llm_obs, scr_obs
        ))

    # Clean set: drop pairs where either side is contaminated OR either
    # observation is a fallback.
    clean_pairs = []
    dropped = 0
    for mp, llm_obs, scr_obs in full_pairs:
        if mp.llm_transcript.game_id in contaminated:
            dropped += 1
            continue
        if mp.scripted_transcript.game_id in contaminated:
            dropped += 1
            continue
        if is_observer_error(llm_obs.free_text) or is_observer_error(scr_obs.free_text):
            dropped += 1
            continue
        clean_pairs.append((mp, llm_obs, scr_obs))

    print(f"Matched pairs — full: {len(full_pairs)}, clean: {len(clean_pairs)}, dropped: {dropped}\n")

    if len(clean_pairs) < 2:
        print("Not enough clean pairs for analysis.")
        return

    # Run Wilcoxon on both samples, side by side.
    full_results = wilcoxon_per_dimension(full_pairs) if len(full_pairs) >= 2 else []
    clean_results = wilcoxon_per_dimension(clean_pairs)

    print("=" * 90)
    print(" WILCOXON SIGNED-RANK TESTS (one-sided, LLM > scripted)  —  FULL vs CLEAN SAMPLE")
    print("=" * 90)
    print(f"\n{'Dimension':<20} {'n_full':>7} {'p_full(BH)':>12} {'r_full':>8}   "
          f"{'n_cln':>6} {'p_cln(BH)':>12} {'r_cln':>8}")
    for r_full, r_clean in zip(full_results, clean_results):
        pf = f"{r_full.p_value_adjusted:.4f}" if r_full.p_value_adjusted is not None else "—"
        pc = f"{r_clean.p_value_adjusted:.4f}" if r_clean.p_value_adjusted is not None else "—"
        print(f"{r_clean.dimension:<20} {r_full.n:>7d} {pf:>12} {r_full.effect_size:>8.2f}   "
              f"{r_clean.n:>6d} {pc:>12} {r_clean.effect_size:>8.2f}")

    # Surface features
    print("\nSurface features on the clean sample:\n")
    llm_feats = [extract_surface_features(mp.llm_transcript, "A") for mp, _, _ in clean_pairs]
    scr_feats = [extract_surface_features(mp.scripted_transcript, "A") for mp, _, _ in clean_pairs]
    summary = pd.DataFrame({
        "LLM_mean": pd.DataFrame(llm_feats).mean(numeric_only=True),
        "Scripted_mean": pd.DataFrame(scr_feats).mean(numeric_only=True),
    })
    summary["gap"] = summary["LLM_mean"] - summary["Scripted_mean"]
    print(summary.round(3).to_string())

    # Regression
    print("\nRegression on the clean sample (HC3 SEs):\n")
    reg_df = regress_gap_on_features(clean_pairs, llm_feats, scr_feats)
    if not reg_df.empty:
        non_const = reg_df[reg_df["feature"] != "const"]
        print(non_const.round({"coefficient": 3, "std_error": 3, "p_value": 4}).to_string(index=False))

    print("\n" + "=" * 90)
    print(" INTERPRETATION")
    print("=" * 90)
    print(
        "\nIf the 'clean' effect sizes and p-values are close to the 'full' values, "
        "the main finding is robust to rate-limit contamination. You can present the "
        "clean numbers and note the filtering in a footnote.\n\n"
        "If the clean numbers are substantially different, you'll want to re-run the "
        "experiment end-to-end with the new rate-limiter in place before presenting."
    )


if __name__ == "__main__":
    main()
