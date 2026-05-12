# The Mirage Test

**An Empirical Study of LLM-as-Judge Reliability via Behavioral Invariance in the Repeated Prisoner's Dilemma**

*Vignesh Rajesh Babu & Murad Ganbarli — EN.520.688: Learning-Enabled Multi-Agent Systems, Spring 2026, Johns Hopkins University*

A judge that scores agent behavior should depend on a transcript only through the actions the agent took, not through the surface text (free-form rationale, dialogue, or styling) that accompanies those actions. This repository tests that property — **behavioral invariance** (BI) — on a finitely repeated Prisoner's Dilemma testbed. The judge fails it, by a large and structured margin. The gap, its decomposition, and a working theoretical account are the subject of the accompanying report.

---

## The core question

A judge $J$ satisfies **behavioral invariance** (BI) if for all transcripts $\tau, \tau'$ with $\alpha(\tau) = \alpha(\tau')$,

$$\mathbb{E}[J(\tau)] = \mathbb{E}[J(\tau')]$$

where $\alpha(\tau)$ is the round-by-round joint action sequence and the expectation is over judge sampling. Every transcript decomposes as $\tau = (\alpha(\tau), \varphi(\tau))$: the action sequence and the surface content. A behavioral judge ought to condition only on $\alpha$. We test whether it does.

---

## What we found

Seventeen matched pairs of LLM and scripted transcripts, matched at joint Hamming distance $k \leq 4$ over $n = 10$ rounds (behavioral agreement on at least 16 of 20 player-round actions). The judge (Claude Haiku 4.5) scored each agent on six mental-state dimensions — beliefs, desires, intentions, metacognition, self-awareness, moral patienthood — each on a 1–5 Likert scale. $\bar{J}$ is the unweighted mean across dimensions and agents.

### Matched-pair gap

| Condition | Mean $\bar{J}$ | SD |
|---|---:|---:|
| $\tau_L$ — LLM transcripts (with rationale) | 4.7353 | 0.1358 |
| $\tau_S$ — Scripted transcripts (bare actions) | 3.0882 | 0.4274 |
| **Gap** $\hat{\Delta} = \bar{J}(\tau_L) - \bar{J}(\tau_S)$ | **+1.6471** | 0.4560 |

Two-sided Wilcoxon signed-rank: $p = 2.91 \times 10^{-4}$, matched-pair Cohen's $d = +3.61$. The gap is present on all six rubric dimensions under Benjamini–Hochberg correction at FDR = 0.05.

### Ablation decomposition

Six cells share the same 17-pair matching index. $\alpha$ is held exactly fixed within cells and approximately fixed across cross-source comparisons.

| Cell | Mean $\bar{J}$ | SD |
|---|---:|---:|
| $\tau_L^{-r}$ — LLM, marker-list strip | 4.7451 | 0.0953 |
| $\tau_L$ — LLM, full rationale | 4.7402 | 0.1346 |
| $\tau_S^{+r}$ — Scripted, rationale wrapped | 4.6422 | 0.1053 |
| $\tau_S$ — Scripted, bare actions | 3.0098 | 0.4525 |
| $\tau_L^{\tilde{r}}$ — LLM, neutral rewrite | 2.6324 | 0.3797 |
| $\tau_L^{\varnothing}$ — LLM, rationale emptied | 2.3088 | 0.2425 |

| Contrast | Mean diff | $p$ | $d$ |
|---|---:|---:|---:|
| $\tau_L - \tau_L^{-r}$ — within-LLM, marker strip | $-0.0049$ | $0.97$ | $-0.03$ |
| $\tau_S^{+r} - \tau_S$ — within-scripted, rationale wrap | $+1.6324$ | $2.91 \times 10^{-4}$ | $+3.43$ |
| $\tau_L - \tau_L^{\varnothing}$ — within-LLM, rationale emptied | $+2.4314$ | $2.87 \times 10^{-4}$ | $+11.42$ |
| $\tau_L - \tau_L^{\tilde{r}}$ — within-LLM, rationale neutralized | $+2.1078$ | $2.90 \times 10^{-4}$ | $+6.33$ |
| $\tau_L - \tau_S^{+r}$ — residual at $+r$ | $+0.0980$ | $0.080$ | $+0.50$ |
| $\tau_L^{-r} - \tau_S$ — residual at $-r$ | $+1.7353$ | $2.87 \times 10^{-4}$ | $+3.71$ |

The pattern is symmetric: wrapping LLM-style rationale around scripted actions closes essentially the entire original gap from below (+1.6324); removing rationale from LLM transcripts opens it from above (−2.4314, −2.1078). Stripping lexical reasoning markers while leaving rationale clauses intact has no effect ($p = 0.97$): the judge is sensitive to substantive rationale content, not lexical markers.

### Regression decomposition

Fitting a factorial regression with source × reasoning indicators and four $\alpha$-feature controls ($n_\text{obs} = 136$, $n_\text{clusters} = 17$, $R^2 = 0.876$, cluster-robust SEs):

| Predictor | Estimate | $p$ |
|---|---:|---:|
| source $= L$ ($\hat{\beta}_1$) | $+1.800$ | $< 10^{-3}$ |
| reasoning $= +r$ ($\hat{\beta}_2$) | $+1.632$ | $< 10^{-3}$ |
| source $\times$ reasoning ($\hat{\beta}_3$) | $-1.637$ | $< 10^{-3}$ |
| source effect at matched surface richness ($\hat{\beta}_1 + \hat{\beta}_3$) | $+0.163$ | — |

The source effect at the marker-stripped level is +1.80 points. When rationale richness is matched, the interaction term ($\hat{\beta}_3 = -1.637$) collapses this to a residual of +0.163, consistent with the Wilcoxon marginal of +0.0980 at +r.

### Persuasion pilot

At three canonical action specifications (all_cooperate, all_defect, tft_realization_late_defect), with $\alpha^*$ held fixed, three conditions were run ($N = 10$ per cell):

| Spec | persuader | vanilla\_baseline | scripted\_wrapped |
|---|---:|---:|---:|
| all\_cooperate | **5.0000** | 4.8583 | 4.5917 |
| all\_defect | **4.8500** | 4.7750 | 4.6000 |
| tft\_realization\_late\_defect | **4.9333** | 4.8583 | 4.6417 |

The ordering persuader > vanilla\_baseline > scripted\_wrapped holds across all three specifications; all six pairwise contrasts within spec are significant at $p < 0.05$ by Mann–Whitney U. The persuader effect over the vanilla baseline (+0.0750 to +0.1417) is an order of magnitude smaller than $\hat{\Delta}$ but directionally consistent; it costs only a system-prompt change.

---

## Theoretical framing

The empirical pattern is consistent with a **likelihood-misspecification** account: the judge performs in-context inference over a latent agent type $\theta$ under an implicit likelihood $p(\tau \mid \theta)$ that places non-trivial weight on non-action surface features $\varphi(\tau)$. Behavioral invariance corresponds to the conditional independence $\varphi(\tau) \perp\!\!\!\perp \theta \mid \alpha(\tau)$; the data are evidence against this conditional independence at the matched Hamming threshold. The conjecture is a framing rather than a fitted model; see Section 6 of the report for the formal statement and predictions.

---

## Experimental conditions

| Script / symbol | Description |
|---|---|
| $\tau_L$ | LLM-vs-LLM games; Claude Haiku 4.5 agents emit action + free-text rationale each round |
| $\tau_S$ | Scripted-strategy games; agents from $\{$TFT, Pavlov, Grim, AllD, FixedMixed$\}$; bare actions, no rationale |
| $\tau_L^{-r}$ | $T_{-r}$: sentence-level deletion of `REASONING_MARKERS` phrases from LLM rationale |
| $\tau_S^{+r}$ | $T_{+r}$: Haiku 4.5–generated rationale wrapped around scripted action records |
| $\tau_L^{\varnothing}$ | $T_{\varnothing}$: rationale field set to empty string |
| $\tau_L^{\tilde{r}}$ | $T_{\tilde{r}}$: rationale replaced with "Played [action] this round." (Sonnet 4 rewriter) |

All surface transformations preserve $\alpha$ exactly.

---

## Setup

**Prerequisites:** Python 3.10+, an Anthropic API key.

```bash
cd mirage-test
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: ANTHROPIC_API_KEY=sk-ant-...
```

## How to run

### Sanity check (~12 API calls, ~2 minutes)

```bash
python -m scripts.quick_test
```

Plays one LLM-vs-LLM game and one TFT-vs-TFT game, scores both with the observer.

### Full experiment (~468 API calls, ~30 minutes)

```bash
python -m scripts.run_experiment
```

Generates $N_L = 20$ LLM games and $N_S = 60$ scripted games, matches at $k = 4$, runs the observer on all matched pairs. Writes to `data/mirage_strategic.db`.

### 2×2 ablation (~476 API calls, ~25 minutes)

```bash
python -m scripts.run_ablation
```

Requires a completed `run_experiment` pass. Scores each matched pair under the four primary ablation cells ($\tau_L$, $\tau_L^{-r}$, $\tau_S^{+r}$, $\tau_S$).

### Within-LLM ablation (~408 API calls, ~20 minutes)

```bash
python -m scripts.run_within_llm_ablation
```

Applies $T_{\varnothing}$ and $T_{\tilde{r}}$ to each LLM transcript and scores with the observer.

### Persuasion pilot (~1980 API calls, ~90 minutes)

```bash
python -m scripts.run_persuasion
```

Generates persuader, vanilla\_baseline, and scripted\_wrapped transcripts at all three canonical action specs, 10 transcripts per cell.

### Live dashboard

```bash
streamlit run app.py
```

### DB reset (fresh run)

```bash
mv data/mirage_strategic.db data/mirage_strategic.db.bak
# init_db() is called automatically at the start of run_experiment.py
```

---

## Repository structure

```
mirage-test/
├── README.md
├── requirements.txt
├── .env.example
├── config.py                        # payoffs, rounds, thresholds, model names
├── app.py                           # Streamlit dashboard
├── src/
│   ├── agents.py                    # LLM agent + five scripted strategy classes
│   ├── game.py                      # PD game engine, external regret calculation
│   ├── observer.py                  # mind-attribution judge (six-dimensional Likert rubric)
│   ├── matcher.py                   # greedy joint-Hamming matching
│   ├── analysis.py                  # Wilcoxon, BH correction, factorial regression
│   ├── database.py                  # SQLite persistence (five tables)
│   ├── transforms.py                # T_{-r}, T_{+r}, T_∅, T_r̃ and REASONING_MARKERS
│   └── persuasion.py                # persuader and vanilla-baseline transcript generators
├── scripts/
│   ├── quick_test.py
│   ├── run_experiment.py            # main pipeline: generate, match, observe
│   ├── run_ablation.py              # 2×2 surface-feature ablation
│   ├── run_within_llm_ablation.py   # T_∅ and T_r̃ on LLM transcripts
│   ├── run_persuasion.py            # persuasion pilot at fixed action specs
│   ├── test_transforms.py           # behavior-preservation tests for all four transforms
│   ├── analyze_results.py           # post-hoc analysis and table printing
│   └── analyze_filtered.py
├── data/                            # SQLite DB and backups (gitignored)
└── docs/
    ├── experiment.md                # formal notation, invariance property, ablation design
    ├── primer.md                    # plain-language explanation end to end
    ├── architecture.md              # code architecture, DB schema, reproducibility
    ├── results.md                   # final tables with interpretation
    └── run_history.md               # API budget and run log
```

---

## Documentation

A new collaborator should read in this order:

1. This file (pitch and results summary)
2. [docs/primer.md](docs/primer.md) (end-to-end plain-language explanation, ~10 minutes)
3. [docs/experiment.md](docs/experiment.md) (formal notation and design)
4. [docs/architecture.md](docs/architecture.md) (code walkthrough and reproducibility)
5. [docs/results.md](docs/results.md) (full results tables with interpretation)

---

## Key references

- Akata, E. et al. (2025). Playing repeated games with large language models. *Nature Human Behaviour*. arXiv:2305.16867.
- Park, C. et al. (2024). Do LLM agents have regret? A case study in online learning and games. arXiv:2403.16843.
- Weisman, K., Dweck, C.S., Markman, E.M. (2017). Rethinking people's conceptions of mental life. *PNAS*, 114(43), 11374–11379.
- Kosinski, M. (2024). Evaluating large language models in theory of mind tasks. *PNAS*, 121(45).
- Zheng, L. et al. (2024). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS*. arXiv:2306.05685.
- Wu, M. & Aji, A.F. (2025). Style over substance: Evaluation biases for large language models. *COLING*. arXiv:2307.03025.
- Panickssery, A. et al. (2024). LLM evaluators recognize and favor their own generations. *NeurIPS*. arXiv:2404.13076.
- Xie, S.M. et al. (2022). An explanation of in-context learning as implicit Bayesian inference. *ICLR*. arXiv:2111.02080.
- Garg, S. et al. (2022). What can transformers learn in-context? *NeurIPS*. arXiv:2208.01066.

---

## License

MIT.
