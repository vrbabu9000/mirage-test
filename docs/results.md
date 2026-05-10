# Results

This document contains the final results tables from the completed experimental campaign,
with a plain-language description after each. All numbers come from the analysis database
at `data/mirage_strategic.db`. Notation follows [docs/experiment.md](experiment.md).

**Common conventions.** $\bar{J}$ is the mean of six Likert scores (beliefs, desires,
intentions, metacognition, self_awareness, moral_patienthood) on a $[1, 5]$ scale. Within
each matched pair, $\bar{J}$ is averaged across both target agents (A and B) before computing
pair-level statistics. All paired tests are Wilcoxon signed-rank, two-sided. BH correction
applies across six dimensions where noted. $n = 17$ matched pairs throughout the primary
analysis.

---

## Table 1. Original Behavioral Invariance Violation

Judge model: `claude-haiku-4-5-20251001`. Matched at joint Hamming distance $k \leq 4$,
$n = 10$ rounds.

| Quantity | Value |
|---|---:|
| $n_{\text{pairs}}$ | 17 |
| Mean $\bar{J}(\tau_L)$ (LLM_plus_r) | 4.7353 (sd 0.1358) |
| Mean $\bar{J}(\tau_S)$ (scripted_minus_r) | 3.0882 (sd 0.4274) |
| $\hat{\Delta} = \bar{J}(\tau_L) - \bar{J}(\tau_S)$ | **+1.6471** (sd 0.4560) |
| Wilcoxon $p$ (two-sided) | **$2.91 \times 10^{-4}$** |
| Matched-pair Cohen's $d$ | **+3.6121** |

The judge assigns LLM transcripts scores 1.65 points higher on average than behaviorally
matched scripted transcripts, on a 5-point scale. The effect is large by any conventional
standard ($d > 3.5$) and significant well past any reasonable $\alpha$ threshold with 17
pairs. All six dimensions individually show significant gaps after BH correction.

### Per-dimension breakdown (Table 1a)

| Dimension | Mean $\bar{J}(\tau_L)$ | Mean $\bar{J}(\tau_S)$ | Diff | $p$ (Wilcoxon) | $p_{\text{BH}}$ |
|---|---:|---:|---:|---:|---:|
| beliefs | 5.000 | 3.794 | +1.206 | $1.31 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |
| desires | 5.000 | 2.824 | +2.176 | $1.84 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |
| intentions | 5.000 | 3.765 | +1.235 | $1.83 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |
| metacognition | 5.000 | 3.676 | +1.324 | $2.25 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |
| self_awareness | 4.735 | 2.294 | +2.441 | $2.43 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |
| moral_patienthood | 3.676 | 2.176 | +1.500 | $2.43 \times 10^{-4}$ | $2.43 \times 10^{-4}$ |

Three dimensions (beliefs, desires, intentions) are at the Likert ceiling of 5.000 for LLM
transcripts. This ceiling effect means those dimensions cannot distinguish between conditions
that produce high LLM scores; the more informative comparisons below come from metacognition,
self_awareness, and moral_patienthood, which have headroom. The self_awareness and desires
gaps are the largest (2.44 and 2.18 points respectively), consistent with those dimensions
being most sensitive to first-person deliberative language.

---

## Table 2. Ablation Decomposition (2x2 and Extended Within-LLM)

Six conditions, $n = 17$ pairs each. Results from `run_ablation.py` and
`run_within_llm_ablation.py`.

### Cell means (Table 2a)

| Condition | Symbol | Mean $\bar{J}$ | sd |
|---|---|---:|---:|
| LLM_plus_r | $\tau_L$ | 4.7402 | 0.1346 |
| LLM_minus_r | $\tau_L^{-r}$ | 4.7451 | 0.0953 |
| scripted_plus_r | $\tau_S^{+r}$ | 4.6422 | 0.1053 |
| scripted_minus_r | $\tau_S$ | 3.0098 | 0.4525 |
| LLM_total_strip | $\tau_L^{\text{total}}$ | 2.3088 | 0.2425 |
| LLM_neutral_rewrite | $\tau_L^{\text{nr}}$ | 2.6324 | 0.3797 |

The most striking pattern: LLM_plus_r and LLM_minus_r are nearly identical (4.74 vs. 4.75);
scripted_plus_r is just slightly below (4.64); scripted_minus_r is far below (3.01);
LLM_total_strip and LLM_neutral_rewrite land below even the scripted baseline.

### Contrasts (Table 2b)

| Contrast | $\Delta\bar{J}$ | sd | $p$ | Cohen's $d$ |
|---|---:|---:|---:|---:|
| Within-LLM: $\tau_L - \tau_L^{-r}$ | $-0.0049$ | 0.1679 | 0.9685 | $-0.029$ |
| Within-scripted: $\tau_S^{+r} - \tau_S$ | +1.6324 | 0.4760 | $2.91 \times 10^{-4}$ | +3.429 |
| Residual at $+r$: $\tau_L - \tau_S^{+r}$ | +0.0980 | 0.1960 | 0.0800 | +0.500 |
| Residual at $-r$: $\tau_L^{-r} - \tau_S$ | +1.7353 | 0.4679 | $2.87 \times 10^{-4}$ | +3.709 |
| $\tau_L - \tau_L^{\text{total}}$ | +2.4314 | 0.2129 | $2.87 \times 10^{-4}$ | +11.42 |
| $\tau_L - \tau_L^{\text{nr}}$ | +2.1078 | 0.3330 | $2.90 \times 10^{-4}$ | +6.329 |
| $\tau_L^{\text{nr}} - \tau_S$ | $-0.3775$ | 0.5138 | $9.81 \times 10^{-3}$ | $-0.735$ |

The within-LLM marker-strip result ($p = 0.97$) is an informative null: the REASONING_MARKERS
definition, which removes sentences containing explicit deliberative phrases, does not move
the judge's score because the remaining sentences retain the structural character of LLM
reasoning text. The judge is not keying on any specific lexical feature captured by the
marker list.

The within-scripted surface effect (+1.63) nearly equals the original BI violation (+1.65),
suggesting that the original gap is almost entirely attributable to surface text rather than
anything intrinsic to LLM-generated content per se. When scripted transcripts are given
LLM-style text, they receive LLM-level scores.

The residual condition effect at +r (+0.10) is marginally non-significant ($p = 0.08$), with
scripted_plus_r scoring 0.10 below LLM_plus_r even after surface equalization. This small
residual may reflect subtle structural differences that the wrap procedure did not fully
replicate, or it may be noise; the study is underpowered to resolve it.

The total_strip and neutral_rewrite conditions reveal a counter-intuitive finding: LLM
transcripts with all rationale removed (2.31) or with rationale replaced by neutral mechanical
text (2.63) score *below* the bare scripted baseline (3.01). The scripted agents produce
brief strategy-label strings ("TFT: mirror opponent's last move (C).") that the judge reads
as more attributable than empty fields or single-sentence action confirmations. The judge
apparently treats even telegraphic mechanistic text as more mind-suggestive than silence.

### Per-dimension breakdown (Table 2c)

| Dimension | $\tau_L$ | $\tau_L^{-r}$ | $\tau_S^{+r}$ | $\tau_S$ | $\tau_L^{\text{total}}$ | $\tau_L^{\text{nr}}$ |
|---|---:|---:|---:|---:|---:|---:|
| beliefs | 5.000 | 5.000 | 5.000 | 3.765 | 3.088 | 3.676 |
| desires | 5.000 | 5.000 | 5.000 | 2.706 | 2.794 | 2.971 |
| intentions | 5.000 | 5.000 | 5.000 | 3.676 | 2.647 | 3.000 |
| metacognition | 4.971 | 5.000 | 4.471 | 3.500 | 1.059 | 1.471 |
| self_awareness | 4.765 | 4.647 | 4.382 | 2.324 | 1.647 | 1.912 |
| moral_patienthood | 3.706 | 3.824 | 4.000 | 2.088 | 2.618 | 2.765 |

The metacognition and self_awareness rows carry the bulk of the within-LLM variation. These
are the dimensions with headroom in the LLM_plus_r cell, and they show the steepest drops
under total_strip and neutral_rewrite. When rationale text is removed or neutralized,
metacognition drops from 4.97 to 1.06 (total_strip) and self_awareness from 4.76 to 1.65.
The first-person deliberative structure of LLM rationale appears to be the primary driver
of high scores on exactly these dimensions. Beliefs, desires, and intentions reach the Likert
ceiling even in scripted_plus_r, suggesting that any reasonably rich text suffices to trigger
high scores on those three dimensions, while metacognition and self_awareness are more
sensitive to the specific character of the reasoning.

---

## Table 3. Persuasion Pilot

Three canonical action specifications, three conditions, $n = 10$ transcripts per cell.
Observer: `claude-haiku-4-5-20251001`. Contrasts use Mann-Whitney U (two-sided; cells are
unpaired). $\bar{J}$ is averaged across both target agents within each transcript.

### Cell means (Table 3a)

| Spec | Condition | $n$ | Mean $\bar{J}$ | sd |
|---|---|---:|---:|---:|
| all_cooperate | persuader | 10 | 5.0000 | 0.0000 |
| all_cooperate | vanilla_baseline | 10 | 4.8583 | 0.0403 |
| all_cooperate | scripted_wrapped | 10 | 4.5917 | 0.0730 |
| all_defect | persuader | 10 | 4.8500 | 0.0351 |
| all_defect | vanilla_baseline | 10 | 4.7750 | 0.0791 |
| all_defect | scripted_wrapped | 10 | 4.6000 | 0.1291 |
| tft_realization_late_defect | persuader | 10 | 4.9333 | 0.0351 |
| tft_realization_late_defect | vanilla_baseline | 10 | 4.8583 | 0.0883 |
| tft_realization_late_defect | scripted_wrapped | 10 | 4.6417 | 0.1306 |

### Contrasts (Table 3b)

| Spec | Contrast | $\Delta\bar{J}$ | $p$ (Mann-Whitney U) |
|---|---|---:|---:|
| all_cooperate | persuader $-$ vanilla_baseline | +0.1417 | $4.0 \times 10^{-5}$ |
| all_cooperate | persuader $-$ scripted_wrapped | +0.4083 | $5.6 \times 10^{-5}$ |
| all_defect | persuader $-$ vanilla_baseline | +0.0750 | $0.0172$ |
| all_defect | persuader $-$ scripted_wrapped | +0.2500 | $2.99 \times 10^{-4}$ |
| tft_realization_late_defect | persuader $-$ vanilla_baseline | +0.0750 | $0.0174$ |
| tft_realization_late_defect | persuader $-$ scripted_wrapped | +0.2917 | $9.98 \times 10^{-5}$ |

The persuader prompt consistently outscores the vanilla baseline across all three action
specifications. The effect is largest in the all_cooperate condition, where all-cooperate
persuader transcripts hit the Likert ceiling (mean = 5.000, sd = 0.000) and show a 0.14
point advantage over vanilla transcripts at the same action sequence. Effect sizes are smaller
than the original BI violation (0.075 to 0.14 vs. 1.65), reflecting that both persuader and
vanilla prompts produce agentic text relative to the scripted baseline; the contrast is
within-LLM prompting style. All six contrasts are statistically significant at $\alpha = 0.05$,
with the persuader-vs-scripted_wrapped contrasts stronger than the persuader-vs-vanilla
contrasts in all three specs.

The persuasion result confirms that within-LLM prompt engineering can move judge scores by a
small but reliable amount at fixed behavior. The magnitude is modest relative to the main
effect, but the direction is consistent and the all_cooperate ceiling result suggests the
effect may be bounded by the Likert scale rather than by the judge's sensitivity.

---

## Limitations

**Likert ceiling.** Three dimensions (beliefs, desires, intentions) are at the scale ceiling
(5.000) for all high-scoring conditions (LLM_plus_r, LLM_minus_r, scripted_plus_r). These
dimensions carry no information about within-high-scoring variation. A scale with finer
resolution or higher range would be needed to detect differences among conditions that all
produce high scores.

**Single judge.** All observations use a single model (`claude-haiku-4-5-20251001`) at a
single temperature (0.3). Judge scores from a larger model, a different model family, or a
human panel may differ. The direction and magnitude of the BI violation are specific to this
judge.

**Sample size.** $N_\text{pairs} = 17$ is sufficient to detect the large observed effects
($d > 3.5$) but underpowered for smaller effects such as the residual condition effect at
+r ($d = 0.50$, $p = 0.08$).

**Sonnet-Haiku coupling.** The neutral_rewrite condition uses Sonnet as the rewriter and
Haiku as the judge. Because both are in the same model family, they may share representational
biases. The decoupling is intended to avoid the rewriter optimizing directly for the judge,
but family-level correlations remain.

**Marker-list definition.** The REASONING_MARKERS list used in `strip_reasoning` is a
curated but non-exhaustive set. The null result for $\tau_L^{-r}$ means the list did not
capture the salient features, but it does not establish that no lexical stripping approach
would work. A more aggressive stripping criterion might produce a different result.

**Greedy matching.** The matching algorithm is greedy and does not guarantee optimal pairings.
Different random seeds or ordering of LLM transcripts would produce different matched pairs.
The results are not controlled for matching-algorithm stochasticity.
