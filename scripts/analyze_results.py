"""Load data from SQLite and run the full statistical analysis.

Prints:
  - Sample sizes per condition
  - Wilcoxon signed-rank test per dimension, with BH correction
  - OLS regression of attribution gap on surface-feature gaps
  - Per-condition summary of surface features

Run with:
    python -m scripts.analyze_results
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config import RUBRIC_DIMENSIONS
from src.analysis import (
    extract_surface_features,
    regress_gap_on_features,
    wilcoxon_per_dimension,
)
from src.database import (
    load_matches,
    load_observation,
    load_transcripts_by_condition,
)
from src.matcher import MatchedPair


def main() -> None:
    llm = {t.game_id: t for t in load_transcripts_by_condition("llm")}
    scripted = {t.game_id: t for t in load_transcripts_by_condition("scripted")}
    matches = load_matches()

    print(f"Loaded: {len(llm)} LLM games, {len(scripted)} scripted games, {len(matches)} matches.")

    pairs_with_scores = []
    llm_features: list[dict] = []
    scripted_features: list[dict] = []

    for llm_gid, scr_gid, dist in matches:
        if llm_gid not in llm or scr_gid not in scripted:
            continue
        # Use agent A from each side for the primary analysis.
        llm_obs = load_observation(llm_gid, "A")
        scr_obs = load_observation(scr_gid, "A")
        if llm_obs is None or scr_obs is None:
            continue
        mp = MatchedPair(llm[llm_gid], scripted[scr_gid], dist)
        pairs_with_scores.append((mp, llm_obs, scr_obs))
        llm_features.append(extract_surface_features(llm[llm_gid], "A"))
        scripted_features.append(extract_surface_features(scripted[scr_gid], "A"))

    print(f"Matched pairs with complete observations: {len(pairs_with_scores)}")
    if len(pairs_with_scores) < 2:
        print("Not enough matched pairs for analysis. Run the experiment longer.")
        return

    # --- Wilcoxon tests -----------------------------------------------------
    print("\n=== Wilcoxon signed-rank tests (one-sided: LLM > scripted) ===")
    results = wilcoxon_per_dimension(pairs_with_scores)
    w_df = pd.DataFrame(
        [
            {
                "dimension": r.dimension,
                "n": r.n,
                "mean_gap": round(r.mean_gap, 3),
                "median_gap": round(r.median_gap, 3),
                "W": round(r.statistic, 2),
                "p": round(r.p_value, 4),
                "p_BH": round(r.p_value_adjusted, 4) if r.p_value_adjusted is not None else None,
                "effect_size": round(r.effect_size, 3),
            }
            for r in results
        ]
    )
    print(w_df.to_string(index=False))

    # --- Surface feature means ---------------------------------------------
    print("\n=== Surface features by condition (means) ===")
    llm_df = pd.DataFrame(llm_features).mean(numeric_only=True).rename("LLM_mean")
    scr_df = pd.DataFrame(scripted_features).mean(numeric_only=True).rename("scripted_mean")
    surf = pd.concat([llm_df, scr_df], axis=1)
    surf["gap"] = surf["LLM_mean"] - surf["scripted_mean"]
    print(surf.round(3).to_string())

    # --- Regression ---------------------------------------------------------
    print("\n=== OLS regression: attribution gap ~ surface feature gaps (HC3 SEs) ===")
    reg_df = regress_gap_on_features(pairs_with_scores, llm_features, scripted_features)
    if len(reg_df) == 0:
        print("  (regression skipped: statsmodels missing or insufficient data)")
    else:
        for dim in RUBRIC_DIMENSIONS:
            sub = reg_df[reg_df["dimension"] == dim]
            if sub.empty:
                continue
            print(f"\n  [{dim}]")
            print(
                sub[["feature", "coefficient", "std_error", "p_value"]]
                .round({"coefficient": 3, "std_error": 3, "p_value": 4})
                .to_string(index=False)
            )


if __name__ == "__main__":
    main()
