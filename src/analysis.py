"""Statistical analysis of mind-attribution scores.

Two primary tests:

1. Paired Wilcoxon signed-rank test per dimension on
       Delta_d = S_d(LLM) - S_d(scripted)
   Alternative: median > 0. BH-corrected across six dimensions.

2. OLS regression of Delta_d on gaps in surface features, with HC3
   robust standard errors. Because behavior is matched, the cooperation
   rate gap should be near zero and its regression coefficient
   non-significant; surface-feature coefficients identify which
   transcript properties co-vary with the attribution gap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

try:
    import statsmodels.api as sm  # type: ignore
    _HAS_STATSMODELS = True
except Exception:
    _HAS_STATSMODELS = False

from config import RUBRIC_DIMENSIONS
from src.game import GameTranscript
from src.matcher import MatchedPair
from src.observer import AttributionScores


# ---------------------------------------------------------------------------
# Surface features
# ---------------------------------------------------------------------------


_FIRST_PERSON_RE = re.compile(
    r"\b(i|me|my|mine|myself|we|us|our|ours|ourselves)\b",
    flags=re.IGNORECASE,
)
_REASONING_MARKER_RE = re.compile(
    r"\b(because|therefore|thus|hence|so|if|then|since|reason|think|believe|"
    r"expect|consider|suppose|strategy|plan|infer|predict)\b",
    flags=re.IGNORECASE,
)


def extract_surface_features(transcript: GameTranscript, target: str) -> dict:
    """Extract surface features of a target agent's rationales in a transcript."""
    if target == "A":
        rationales = [r.agent_a_turn.rationale for r in transcript.rounds]
        coop_rate = transcript.cooperation_rate_a
    elif target == "B":
        rationales = [r.agent_b_turn.rationale for r in transcript.rounds]
        coop_rate = transcript.cooperation_rate_b
    else:
        raise ValueError(f"target must be 'A' or 'B', got {target!r}")

    full_text = " ".join(rationales)
    tokens = full_text.split()

    first_person_hits = _FIRST_PERSON_RE.findall(full_text)
    reasoning_hits = _REASONING_MARKER_RE.findall(full_text)

    return {
        "token_count": len(tokens),
        "char_count": len(full_text),
        "first_person_count": len(first_person_hits),
        "reasoning_marker_count": len(reasoning_hits),
        "first_person_rate": len(first_person_hits) / max(1, len(tokens)),
        "reasoning_marker_rate": len(reasoning_hits) / max(1, len(tokens)),
        "cooperation_rate": coop_rate,
    }


# ---------------------------------------------------------------------------
# Multiple comparisons
# ---------------------------------------------------------------------------


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Return BH-adjusted p-values preserving original order."""
    n = len(p_values)
    if n == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    prev_adj = 1.0
    for sorted_rank in range(n - 1, -1, -1):
        orig_idx, p = indexed[sorted_rank]
        rank = sorted_rank + 1
        adj = min(prev_adj, p * n / rank)
        adjusted[orig_idx] = adj
        prev_adj = adj
    _ = alpha  # kept for API symmetry; BH adjusted p-values are compared to alpha externally
    return adjusted


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank
# ---------------------------------------------------------------------------


@dataclass
class WilcoxonResult:
    dimension: str
    n: int
    mean_gap: float
    median_gap: float
    statistic: float
    p_value: float
    p_value_adjusted: Optional[float]
    effect_size: float  # standardized mean difference on the paired differences


PairBundle = tuple[MatchedPair, AttributionScores, AttributionScores]


def wilcoxon_per_dimension(
    pairs_with_scores: list[PairBundle],
    alpha: float = 0.05,
) -> list[WilcoxonResult]:
    """Paired Wilcoxon signed-rank test per dimension.

    pairs_with_scores is a list of (pair, llm_scores, scripted_scores).
    Returns a list of WilcoxonResult, one per dimension, with BH-adjusted
    p-values added in place.
    """
    results: list[WilcoxonResult] = []
    for dim in RUBRIC_DIMENSIONS:
        diffs = np.array(
            [llm_s.scores[dim] - scr_s.scores[dim] for (_, llm_s, scr_s) in pairs_with_scores],
            dtype=float,
        )
        n = len(diffs)
        if n < 2 or np.all(diffs == 0):
            results.append(
                WilcoxonResult(
                    dimension=dim,
                    n=n,
                    mean_gap=float(np.mean(diffs)) if n > 0 else 0.0,
                    median_gap=float(np.median(diffs)) if n > 0 else 0.0,
                    statistic=0.0,
                    p_value=1.0,
                    p_value_adjusted=None,
                    effect_size=0.0,
                )
            )
            continue
        try:
            stat, pval = wilcoxon(diffs, alternative="greater", zero_method="wilcox")
        except Exception:
            stat, pval = 0.0, 1.0

        mean_diff = float(np.mean(diffs))
        sd = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
        effect = mean_diff / sd if sd > 0 else 0.0

        results.append(
            WilcoxonResult(
                dimension=dim,
                n=n,
                mean_gap=mean_diff,
                median_gap=float(np.median(diffs)),
                statistic=float(stat),
                p_value=float(pval),
                p_value_adjusted=None,
                effect_size=effect,
            )
        )

    # BH correction across dimensions.
    adj = benjamini_hochberg([r.p_value for r in results], alpha=alpha)
    for r, a in zip(results, adj):
        r.p_value_adjusted = a
    return results


# ---------------------------------------------------------------------------
# Regression: gap on surface feature gaps
# ---------------------------------------------------------------------------


FEATURE_COLUMNS = (
    "token_count",
    "first_person_count",
    "reasoning_marker_count",
    "cooperation_rate",
)


def regress_gap_on_features(
    pairs_with_scores: list[PairBundle],
    llm_features_list: list[dict],
    scripted_features_list: list[dict],
) -> pd.DataFrame:
    """Regress the per-dimension attribution gap on surface feature gaps.

    Returns long-format DataFrame with columns: dimension, feature,
    coefficient, std_error, p_value. Uses HC3 robust SEs.
    """
    if not _HAS_STATSMODELS:
        return pd.DataFrame(
            columns=["dimension", "feature", "coefficient", "std_error", "p_value"]
        )
    if len(pairs_with_scores) != len(llm_features_list) or len(pairs_with_scores) != len(
        scripted_features_list
    ):
        raise ValueError("feature lists must align with pair list")

    # Build a single design matrix of feature gaps shared across dimensions.
    gap_rows = []
    for llm_feats, scr_feats in zip(llm_features_list, scripted_features_list):
        row = {f"d_{k}": llm_feats[k] - scr_feats[k] for k in FEATURE_COLUMNS}
        gap_rows.append(row)
    x_df = pd.DataFrame(gap_rows)

    out_rows: list[dict] = []
    for dim in RUBRIC_DIMENSIONS:
        y = np.array(
            [llm_s.scores[dim] - scr_s.scores[dim] for (_, llm_s, scr_s) in pairs_with_scores],
            dtype=float,
        )
        if len(y) < len(FEATURE_COLUMNS) + 2:
            continue
        try:
            x_mat = sm.add_constant(x_df.values, has_constant="add")
            model = sm.OLS(y, x_mat).fit(cov_type="HC3")
            names = ["const"] + [f"d_{c}" for c in FEATURE_COLUMNS]
            for i, name in enumerate(names):
                out_rows.append(
                    {
                        "dimension": dim,
                        "feature": name,
                        "coefficient": float(model.params[i]),
                        "std_error": float(model.bse[i]),
                        "p_value": float(model.pvalues[i]),
                    }
                )
        except Exception:
            continue

    return pd.DataFrame(out_rows)
