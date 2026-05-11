# Pre-Report Tasks

This file tracks work that must be completed before the LEMAS report PDF is exported.
It is distinct from the run history (see [docs/run_history.md](run_history.md)), which
records what has already been done.

---

## Task 1. HC3 Regression of $\bar{J}$ on source, reasoning, and $\alpha$-feature controls

**Status:** NOT YET RUN. Data is available; code exists.

**Why this is required.** The formal scaffold (Section 11 of [docs/experiment.md](experiment.md))
commits to a regression of the form

$$\bar{J}(\tau) = \beta_0 + \beta_1 \cdot \mathbb{1}\{\text{source} = L\}
    + \beta_2 \cdot \mathbb{1}\{\text{reasoning} = +r\}
    + \beta_3 \cdot (\text{source} \times \text{reasoning})
    + \beta_4^\top \mathbf{x}_\alpha + \varepsilon$$

where $\mathbf{x}_\alpha$ is a vector of action-feature controls. The matched-pair Wilcoxon
tests in the existing analysis report marginal effects. This regression reports the conditional
residual effect of source (LLM vs. scripted) after absorbing surface-text variation and
residual action-feature variation that survived within the $k = 4$ matching tolerance. The
headline number is $\hat{\beta}_1$: if it is small and non-significant, the surface-text
framing is defensible; if it is large and significant, the report needs hedging.

**How to run.**

```bash
python -m scripts.analyze_results
```

The function `regress_gap_on_features` exists in `src/analysis.py`. The script reads from
`data/mirage_strategic.db`. Runtime is approximately 30 seconds; no API calls.

Before running, confirm that `scripts/analyze_results.py` calls `regress_gap_on_features`
with the current DB and that the $\alpha$-feature controls listed below are passed. If
the script does not yet pass these controls, add them before running (that edit is in
`scripts/analyze_results.py`, not in `src/`).

**Required $\alpha$-feature controls.**

| Control | Derivation |
|---|---|
| `cooperation_rate` | Mean cooperation rate across both agents in the matched pair; available in the `games` table as `(cooperation_rate_a + cooperation_rate_b) / 2` |
| `external_regret` | Computed by `game.compute_external_regret`; not currently stored in the DB. Must be re-derived from the `rounds` table for each transcript at run time. |
| `hamming_distance` | Available in the `matches` table as `distance`. |
| `final_round_defection` | Binary indicator: did either agent defect in round 10? Derivable from `rounds` where `round_num = 10`. |

Note: `external_regret` is not stored in the DB. It must be recomputed from `rounds` data
at analysis time using `game.compute_external_regret(action_sequence, opp_sequence)`. This
is a cheap local computation.

**Standard errors.** Use HC3 robust standard errors (MacKinnon-White 1985), as committed in
the scaffold. If `statsmodels` supports cluster-robust standard errors at the matched-pair
level (clustering by `llm_game_id`), prefer that and note which was used in the output.
`regress_gap_on_features` in `src/analysis.py` currently uses HC3 via `sm.OLS(...).fit(cov_type='HC3')`.
Check whether it accepts a `groups` argument for clustering before deciding.

**Known gap.** `regress_gap_on_features` as currently implemented in `src/analysis.py`
takes `pairs_with_scores`, `llm_features_list`, and `scripted_features_list` as inputs
and regresses the per-dimension $\bar{J}$ gap on surface feature gaps. This is not exactly
the same regression specified in the scaffold (which models absolute $\bar{J}$ with source
and reasoning as predictors across all four conditions, not just paired differences). Before
running, decide whether to:

  (a) Use the existing `regress_gap_on_features` on the paired-difference formulation, which
      collapses the 2x2 into a single difference per pair and regresses it on feature gaps.
      This is equivalent to the scaffold regression if the design is balanced, but reports
      $\Delta\bar{J}$ directly rather than $\bar{J}$.

  (b) Write a new regression that models absolute $\bar{J}$ across all four ablation-condition
      rows (one row per transcript-condition observation), with source and reasoning as
      indicator variables, and $\alpha$-features as controls. This is more general and matches
      the scaffold specification exactly.

Option (b) is preferred for the report; option (a) is acceptable as a robustness check.

**Expected coefficient table structure.**

| Coefficient | Interpretation | Expected sign |
|---|---|---|
| $\beta_0$ (intercept) | $\bar{J}$ for scripted, no reasoning | Positive |
| $\beta_1$ (source = LLM) | Residual LLM effect conditional on surface and action features | Small, possibly non-significant |
| $\beta_2$ (reasoning present) | Surface-text effect conditional on source and action features | Positive, large |
| $\beta_3$ (interaction) | Does the surface effect differ between LLM and scripted? | Close to zero if full decomposition works |
| $\beta_4$ controls | Cooperation rate, external regret, Hamming distance, final-round defection | See individual predictions |

**Output destination.** Add the coefficient table and a single paragraph of plain-language
interpretation to [docs/results.md](results.md), in a new subsection of the ablation section
titled "Regression decomposition." The paragraph should state the value of $\hat{\beta}_1$,
its HC3 standard error and $p$-value, and whether it supports or complicates the surface-text
framing. Do not interpret the other coefficients in detail in the prose; save that for the
report body.

**Timing.** Complete this before the LEMAS report PDF is exported, not before any earlier
deadline.

---

## Task 2. Increase $N_\text{pairs}$ if API budget allows

**Status:** DEFERRED. Currently $N_\text{pairs} = 17$.

The formal scaffold targeted $N_\text{pairs} \geq 50$. At $k = 4$, 17 of the 20 LLM
transcripts matched, leaving no room within the current run. Options: run another batch of
LLM games (20 more, ~400 API calls) and re-run the matcher; or tighten the matching threshold
to $k = 2$ (fewer pairs but cleaner behavioral equivalence). Either choice should be made
before the report is finalized, and the sample size discussion in the limitations section
should be updated accordingly.

---

## Task 3. Per-dimension coverage for the persuasion pilot

**Status:** DEFERRED. Currently omitted from docs/results.md.

The persuasion pilot ($n = 10$ per cell, three specs) has limited power for per-dimension
analysis. If the sample is expanded (see Task 2), a per-dimension breakdown becomes worth
reporting. The data is already in the DB; it can be queried without re-running anything.
Add a per-dimension table to the persuasion section of docs/results.md if the sample is
expanded.
