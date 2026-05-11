# Regression Robustness Handoff: Restricted Model (External Regret Dropped)

**No anomalies. The headline interpretation in the original handoff stands.**

---

## 1. Rationale for the robustness check

The full factorial regression reported in docs/regression_handoff.md included four
α-feature controls: `cooperation_rate`, `external_regret`, `final_round_defection`, and
`hamming_distance`. Post-estimation diagnostics revealed a near-perfect collinearity between
`cooperation_rate` and `external_regret` (Pearson $r = 0.994$, VIF 110 and 106
respectively). This collinearity is structural: in a finitely repeated Prisoner's Dilemma,
an agent who cooperates frequently against cooperative opponents accrues exactly the
"missed-defection" opportunity that drives external regret upward. The two controls are
functionally redundant in this dataset, and their individual coefficient estimates and
$p$-values in the full model are unreliable.

This robustness check drops `external_regret` and refits the same factorial structure on the
same 136 observations with the same cluster-robust standard errors (17 matched-pair clusters).
The test question is whether $\hat{\beta}_1$ (source effect) and $\hat{\beta}_3$ (source
× reasoning interaction) shift by more than one standard error when the redundant control is
removed. If not, the collinearity was benign for the headline claims.

---

## 2. Restricted-model coefficient table

Specification:

$$\bar{J}(\tau) = \beta_0 + \beta_1 \cdot \mathbb{1}\{\text{source} = L\}
    + \beta_2 \cdot \mathbb{1}\{\text{reasoning} = +r\}
    + \beta_3 \cdot \bigl(\mathbb{1}\{\text{source}=L\} \times \mathbb{1}\{\text{reasoning}=+r\}\bigr)
    + \beta_4 \cdot \text{cooperation\_rate}
    + \beta_5 \cdot \text{final\_round\_defection}
    + \beta_6 \cdot \text{hamming\_distance} + \varepsilon$$

All continuous controls standardized (mean 0, sd 1). Cluster-robust SEs at matched-pair
level (17 clusters, $df = 16$).

| Term | Estimate | Std. Error | $t$ | $p$-value | 95% CI lower | 95% CI upper |
|---|---:|---:|---:|---:|---:|---:|
| intercept | 3.007 | 0.112 | 26.895 | $< 0.001$ | 2.788 | 3.226 |
| source\_L ($\hat{\beta}_1$) | **+1.743** | 0.126 | 13.847 | **$< 0.001$** | 1.497 | 1.990 |
| reasoning\_plus\_r ($\hat{\beta}_2$) | **+1.632** | 0.118 | 13.821 | **$< 0.001$** | 1.401 | 1.864 |
| source $\times$ reasoning ($\hat{\beta}_3$) | **$-$1.637** | 0.131 | $-$12.541 | **$< 0.001$** | $-$1.893 | $-$1.381 |
| cooperation\_rate | $+$0.048 | 0.029 | 1.683 | $0.093$ | $-$0.008 | $+$0.104 |
| final\_round\_defection | $-$0.002 | 0.080 | $-$0.021 | $0.983$ | $-$0.158 | $+$0.155 |
| hamming\_distance | $-$0.025 | 0.029 | $-$0.870 | $0.384$ | $-$0.081 | $+$0.031 |

Note on cooperation\_rate sign reversal: the coefficient changed from $-0.578$ in the full
model to $+0.048$ in the restricted model. This sign reversal is a textbook consequence of
removing a near-perfectly collinear predictor. `external_regret` ($r = 0.994$ with
`cooperation_rate`) was suppressing the latter's coefficient in the full model; with it
removed, the direction is positive and more interpretable (higher cooperation rate
marginally associated with higher $\bar{J}$), though the coefficient remains non-significant
($p = 0.093$). This does not affect the headline estimates.

---

## 3. Stability check: full vs. restricted model

| Quantity | Full model | Restricted model | $\Delta$ estimate | $\Delta$ SE |
|---|---:|---:|---:|---:|
| intercept | 3.007 | 3.007 | $-0.001$ | $+0.006$ |
| $\hat{\beta}_1$ (source\_L) | +1.800 | +1.743 | $-0.057$ | $+0.037$ |
| $\hat{\beta}_2$ (reasoning\_plus\_r) | +1.632 | +1.632 | $\phantom{-}0.000$ | $-0.001$ |
| $\hat{\beta}_3$ (source $\times$ reasoning) | $-$1.637 | $-$1.637 | $\phantom{-}0.000$ | $-0.001$ |
| $R^2$ | 0.876 | 0.870 | $-0.006$ | — |

**Stability test.** For each headline coefficient, the question is whether $|\Delta\hat{\beta}|$
exceeds the full-model standard error.

| Coefficient | $|\Delta\hat{\beta}|$ | Full-model SE | Within 1 SE? |
|---|---:|---:|---|
| $\hat{\beta}_1$ (source\_L) | 0.057 | 0.089 | **Yes** (ratio = 0.64) |
| $\hat{\beta}_3$ (source $\times$ reasoning) | 0.000 | 0.131 | **Yes** (ratio ≈ 0.00) |

Both headline coefficients shift by less than one full-model standard error. The collinearity
between `cooperation_rate` and `external_regret` was benign for the main estimates.

The source effect at reasoning $= +r$ in the restricted model:

$$\hat{\beta}_1 + \hat{\beta}_3 = 1.743 - 1.637 = +0.106$$

Compared to $+0.163$ in the full model — a shift of $-0.057$, the same as the shift in
$\hat{\beta}_1$. Both are in the same direction and the residual LLM advantage at matched
surface richness remains small and non-significant at $p = 0.08$ (Wilcoxon) in either
specification.

---

## 4. Diagnostic block — restricted model

### VIFs

| Predictor | VIF (restricted) | VIF (full) | Change |
|---|---:|---:|---|
| source\_L | 3.02 | 3.24 | $-0.22$ |
| reasoning\_plus\_r | 2.00 | 2.00 | $\phantom{-}0.00$ |
| source $\times$ reasoning | 3.00 | 3.00 | $\phantom{-}0.00$ |
| cooperation\_rate | **2.02** | 109.82 | $-107.80$ |
| final\_round\_defection | 3.31 | 3.50 | $-0.19$ |
| hamming\_distance | 1.11 | 1.31 | $-0.20$ |

All VIFs in the restricted model are below 3.5. The collinearity issue is fully resolved by
dropping `external_regret`.

### Pearson correlations of cooperation\_rate with retained controls

| Control | $r$ with cooperation\_rate |
|---|---:|
| source\_L | $-0.073$ |
| reasoning\_plus\_r | $\phantom{-}0.000$ |
| source $\times$ reasoning | $-0.042$ |
| final\_round\_defection | $-0.610$ |
| hamming\_distance | $-0.145$ |

The $r = -0.610$ between `cooperation_rate` and `final_round_defection` is moderate: agents
with high cooperation rates are less likely to defect in the final round. This is expected
game behavior (cooperators cooperate throughout) and does not create multicollinearity; the
VIF for `final_round_defection` is 3.31.

---

## 5. How to use this in the report

**Does the headline interpretation in the original §5.3 need updating?**
No. Both $\hat{\beta}_1$ and $\hat{\beta}_3$ are stable within one standard error across
specifications. The prose in the original regression handoff — "the source effect collapses
from 1.80 to 0.16 points when surface text is equalized" — remains accurate. The restricted
model narrows this slightly to $1.743 - 1.637 = 0.106$, which rounds to the same conclusion.

**Recommended slot for the restricted-model table.** Place the restricted-model coefficient
table in an appendix (e.g., Appendix A, "Robustness specifications"). In §5.3, add one
sentence at the close of the regression subsection:

> "A restricted model dropping `external_regret` (which is near-perfectly collinear with
> cooperation rate in this dataset, $r = 0.994$) yields $\hat{\beta}_1 = +1.743$ and
> $\hat{\beta}_3 = -1.637$, shifts of less than one standard error from the full-model
> estimates; see Appendix A."

**Does the abstract need updating?** No. The abstract cites the direction and significance
of the source collapse, not a specific point estimate for $\hat{\beta}_1$. Both
specifications support the same qualitative claim.

**Preferred specification for the body of the paper.** The restricted model is cleaner
(all VIFs $\leq 3.31$, no anomalous sign flip on a control, $R^2 = 0.870$) and should be
the specification cited in §5.3. The full model appears in Appendix A as the original run
with the collinearity diagnostic noted.
