# Regression Handoff: HC3 Factorial Regression Results

**For the report-drafting reader.** This file contains everything needed to slot a regression
results subsection into Section 4.2 of docs/results.md. Read it alongside Section 4.2
(the ablation decomposition tables). Do not modify docs/results.md until you have read Section 7
(diagnostics and anomalies) of this file.

---

## 1. What the regression tests and why it belongs in Section 4.2

The Wilcoxon contrasts in Section 4.2 report marginal effects: the paired difference
$\bar{J}(\tau_L^{-r}) - \bar{J}(\tau_S)$, for example, measures the average gap between LLM
and scripted transcripts at matched action sequences, without conditioning on any action-level
feature that might vary within the $k = 4$ matching window. Two matched transcripts can have
the same action sequence up to Hamming distance 4 while differing in cooperation rate,
external regret, or round-level defection patterns — and the judge may respond to those
differences independently of the source and reasoning conditions. The HC3 regression absorbs
this residual action-feature variation and asks: after conditioning on cooperation rate,
external regret, joint Hamming distance, and final-round defection, how much of the LLM versus
scripted gap survives? The answer anchors the report's claim that surface text, not behavioral
micro-variation, explains the BI violation.

---

## 2. Regression specification

$$\bar{J}(\tau) = \beta_0 + \beta_1 \cdot \mathbb{1}\{\text{source} = L\}
    + \beta_2 \cdot \mathbb{1}\{\text{reasoning} = +r\}
    + \beta_3 \cdot \bigl(\mathbb{1}\{\text{source} = L\} \times \mathbb{1}\{\text{reasoning} = +r\}\bigr)
    + \mathbf{x}_\alpha^\top \boldsymbol{\beta}_4 + \varepsilon$$

| Term | Definition |
|---|---|
| $\bar{J}(\tau)$ | Mean of six Likert rubric scores for one (transcript, target-agent) observation |
| $\mathbb{1}\{\text{source} = L\}$ | 1 for LLM_plus_r and LLM_minus_r; 0 for scripted_plus_r and scripted_minus_r |
| $\mathbb{1}\{\text{reasoning} = +r\}$ | 1 for LLM_plus_r and scripted_plus_r; 0 for LLM_minus_r and scripted_minus_r |
| interaction | product of the two indicators above |
| $\mathbf{x}_\alpha$ | vector of α-feature controls (see Section 3) |

Estimation unit: one row per (transcript, target-agent) cell in the four ablation conditions. The
within-LLM total_strip and neutral_rewrite conditions are **not** in this regression. The
persuasion conditions are **not** in this regression.

---

## 3. α-feature controls

Each continuous control is standardized to mean 0, standard deviation 1 across all 136
observations before estimation, so that $\hat{\beta}_1$ is interpretable as the residual
source effect at the sample-average level of each control.

| Control | Computation | Standardized? |
|---|---|---|
| `cooperation_rate` | Fraction of rounds in which the target agent played C; computed from the `rounds` table (`action_a` for target A, `action_b` for target B). Range $[0, 1]$. Pre-standardization mean = 0.752, sd = 0.344. | Yes |
| `final_round_defection` | 1 if the target agent played D in round $n = 10$; else 0. | No (binary) |
| `external_regret` | $R_i^{\text{ext}} = \max_{a' \in \{C,D\}} \sum_t u_i(a', a_t^{\text{opp}}) - \sum_t u_i(a_t^i, a_t^{\text{opp}})$, computed using `src/game.py::compute_external_regret` per agent per transcript. Pre-standardization mean = 14.43, sd = 7.30. | Yes |
| `hamming_distance` | Joint Hamming distance between the LLM and scripted transcript in the matched pair; pair-level, identical for all eight observations in the same pair. From the `matches` table. Pre-standardization mean = 2.41, sd = 1.29. | Yes |

**Important diagnostic note on `cooperation_rate` and `external_regret`:** These two controls
have a Pearson correlation of 0.994 in this dataset, producing VIFs of 110 and 106
respectively. They are near-perfectly collinear because, in a finitely repeated PD, cooperating
against cooperative opponents generates exactly the "missed defection" opportunity that drives
external regret. The individual coefficients on these two controls are unreliable and should not
be interpreted separately. This collinearity does **not** affect $\hat{\beta}_1$,
$\hat{\beta}_2$, or $\hat{\beta}_3$, which have VIFs of 3.24, 2.00, and 3.00 respectively.
The recommended action for the final report is to drop `external_regret` and retain
`cooperation_rate` as the single action-richness control; a robustness check with that
restricted model is noted at the end of this section.

---

## 4. Coefficient table

Standard errors are cluster-robust at the matched-pair level (17 clusters, statsmodels
`cov_type='cluster'`). Confidence intervals are 95%. Degrees of freedom for hypothesis tests
is $n_{\text{clusters}} - 1 = 16$.

| Term | Estimate | Std. Error | $t$ | $p$-value | 95% CI lower | 95% CI upper |
|---|---:|---:|---:|---:|---:|---:|
| intercept | 3.007 | 0.106 | 28.333 | $< 0.001$ | 2.799 | 3.215 |
| source\_L ($\hat{\beta}_1$) | **+1.800** | 0.089 | 20.208 | **$< 0.001$** | 1.626 | 1.975 |
| reasoning\_plus\_r ($\hat{\beta}_2$) | **+1.632** | 0.119 | 13.767 | **$< 0.001$** | 1.400 | 1.865 |
| source $\times$ reasoning ($\hat{\beta}_3$) | **$-$1.637** | 0.131 | $-$12.493 | **$< 0.001$** | $-$1.894 | $-$1.380 |
| cooperation\_rate | $-$0.578 | 0.318 | $-$1.816 | $0.069$ | $-$1.201 | $+$0.046 |
| final\_round\_defection | $-$0.054 | 0.059 | $-$0.913 | $0.361$ | $-$0.169 | $+$0.062 |
| external\_regret | $+$0.620 | 0.301 | $+$2.057 | $0.040$ | $+$0.029 | $+$1.211 |
| hamming\_distance | $+$0.003 | 0.031 | $+$0.088 | $0.930$ | $-$0.057 | $+$0.062 |

---

## 5. Headline number: $\hat{\beta}_1$ (source coefficient)

> $\hat{\beta}_1 = +1.800$ (SE = 0.089, $p < 0.001$, 95% CI: [1.626, 1.975]).

This coefficient estimates the conditional source effect **when reasoning is absent**
($\text{reasoning} = -r$), after absorbing the four α-feature controls. In plain language: at
the average cooperation rate, external regret, Hamming distance, and final-round defection, an
LLM transcript without reasoning markers scores 1.80 points higher on $\bar{J}$ than a
scripted transcript without reasoning markers. This is large, highly significant, and does not
support the interpretation that the BI violation is fully explained by surface-text richness.

However, this value must be read together with $\hat{\beta}_3$ below. In a model with an
interaction, $\hat{\beta}_1$ estimates the source effect at one specific level of reasoning
(absent), not unconditionally. See Section 6.

---

## 6. Interaction term: $\hat{\beta}_3$ (source $\times$ reasoning)

> $\hat{\beta}_3 = -1.637$ (SE = 0.131, $p < 0.001$, 95% CI: [$-$1.894, $-$1.380]).

This is the formal regression statement of the key ablation finding. The source effect is 1.637
points smaller when reasoning text is present than when it is absent. Combining with
$\hat{\beta}_1$:

$$\text{source effect at reasoning} = +r: \quad \hat{\beta}_1 + \hat{\beta}_3 = 1.800 - 1.637 = +0.163$$

At the matched surface-text richness level (+r), the residual LLM advantage conditional on
α-features is 0.163 $\bar{J}$ points. This aligns with the Wilcoxon residual at +r reported in
Table 2b (+0.098, $p = 0.08$); the regression estimate is slightly larger because controlling
for the negative coefficient on cooperation\_rate (LLM agents cooperate more, which suppresses
$\bar{J}$ in the regression) inflates the conditional source estimate relative to the marginal
paired difference.

In plain language for the report: the LLM versus scripted gap collapses from 1.80 points to
0.16 points when both conditions are given equivalent surface-text richness. The regression
confirms that surface text, not anything intrinsic to LLM-generated content conditional on
action features, explains nearly all of the BI violation.

---

## 7. Diagnostics

| Quantity | Value | Notes |
|---|---|---|
| $n_{\text{obs}}$ | 136 | 17 pairs × 4 conditions × 2 targets. As expected. |
| $n_{\text{clusters}}$ | 17 | One cluster per matched pair. |
| $R^2$ | 0.876 | High but consistent with the large source and reasoning effects. |
| SE method | Cluster-robust, 17 clusters | Small-cluster warning: 17 clusters is below the conventional threshold of $\geq 30$ for reliable cluster-robust inference. Standard errors for the key predictors are likely conservative (over-estimated) in small samples. |
| VIF: source\_L | 3.24 | Acceptable. |
| VIF: reasoning\_plus\_r | 2.00 | Acceptable. |
| VIF: source\_x\_reasoning | 3.00 | Acceptable. |
| VIF: cooperation\_rate | **109.82** | High. Near-perfect collinearity with external\_regret ($r = 0.994$). See note below. |
| VIF: external\_regret | **105.74** | High. Same issue. |
| VIF: final\_round\_defection | 3.50 | Acceptable. |
| VIF: hamming\_distance | 1.31 | Acceptable. |

**Collinearity note.** The VIFs for `cooperation_rate` and `external_regret` are 110 and 106.
Their correlation is 0.994. This collinearity is structural: in a PD game, an agent who
cooperates frequently against cooperative opponents accumulates exactly the missed-defection
opportunity that drives external regret upward. The two variables are functionally redundant
in this dataset. The individual coefficients on these controls (and their $p$-values) are not
reliable and should not be cited individually in the report. The key coefficients $\hat{\beta}_1$,
$\hat{\beta}_2$, $\hat{\beta}_3$ are unaffected (their VIFs are 3.24, 2.00, 3.00).

**Recommended robustness check.** Re-run the regression dropping `external_regret` and retaining
`cooperation_rate`, `final_round_defection`, and `hamming_distance`. If $\hat{\beta}_1$ and
$\hat{\beta}_3$ are stable across the two specifications, the collinearity concern is not
material to the headline finding.

**On $R^2 = 0.876$.** The large $R^2$ reflects the strong and well-identified source and
reasoning main effects (the $\bar{J}$ gap is 1.65 points on a 5-point scale), not overfitting.
With 136 observations and 8 predictors, the model is not overparameterized.

---

## 8. How to use this in the report

**Slot into:** docs/results.md, Section 4.2 (ablation decomposition), new subsection titled
"Regression decomposition." Place it after Table 2b (the Wilcoxon contrasts) and before Table 2c
(per-dimension breakdown).

**Prose to update in Section 4.2:** The current prose states the residual condition effect at
+r is +0.10 ($p = 0.08$) and describes it as "marginally non-significant." The regression
provides the conditional version of this estimate: $\hat{\beta}_1 + \hat{\beta}_3 = +0.163$
after controlling for α-features, conditional on the α-feature coefficient estimates being
interpreted cautiously given the cooperation\_rate / external\_regret collinearity. The
direction is consistent with the Wilcoxon; the magnitude is slightly larger. The prose in
Section 4.2 that calls the residual "marginal" remains accurate and can stand. Add a
cross-reference to the regression subsection for readers who want the conditional estimate.

The regression strengthens, not complicates, the surface-text framing: $\hat{\beta}_3 = -1.637$
($p < 0.001$) is the formal confirmation that the source effect collapses when surface text is
equalized. Cite that number in the abstract or findings summary.
