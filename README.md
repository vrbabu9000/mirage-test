# The Mirage Test

**LLM-as-Judge Reliability Under Behavioral Invariance in Repeated Prisoner's Dilemma Play**

A LEMAS (Learning-Enabled Multi-Agent Systems) final project at Johns Hopkins. This repository
tests whether an LLM judge satisfies a natural reliability requirement: two transcripts that
describe the same sequence of game actions should receive the same expected score. They do not.
The gap, and its decomposition, are the subject of this study.

---

## The core question

A judge $J$ satisfies **behavioral invariance** (BI) if transcripts sharing the same
action sequence $\alpha$ receive the same expected score, regardless of the surrounding text.
This is a minimal consistency requirement for any evaluation pipeline that claims to measure
behavior. Does the LLM judge used here satisfy it? Empirically: no, by a large and highly
significant margin.

---

## What we found

Seventeen matched pairs of LLM and scripted transcripts, matched at joint Hamming distance
$k \leq 4$ over $n = 10$ rounds. The observer (Claude Haiku) scored each agent on six
dimensions of mental-state attribution (beliefs, desires, intentions, metacognition,
self_awareness, moral_patienthood) on a 1-5 Likert scale. $\bar{J}$ is the mean across
the six dimensions.

### Headline results

| Contrast | $\Delta\bar{J}$ | $p$ (Wilcoxon) | Cohen's $d$ |
|---|---:|---:|---:|
| LLM_plus_r vs scripted_minus_r (original BI violation) | +1.65 | $2.9 \times 10^{-4}$ | +3.61 |
| Within-LLM: strip reasoning markers ($\tau_L$ vs $\tau_L^{-r}$) | $-0.005$ | $0.97$ | $-0.03$ |
| Within-scripted: wrap rationale ($\tau_S^{+r}$ vs $\tau_S$) | +1.63 | $2.9 \times 10^{-4}$ | +3.43 |
| Residual condition effect at matched surface richness (+r) | +0.10 | $0.08$ | +0.50 |
| LLM vs LLM with all rationale removed ($\tau_L^{\text{total}}$) | +2.43 | $2.9 \times 10^{-4}$ | +11.4 |
| LLM vs LLM with neutral rewrite (Sonnet rewriter) | +2.11 | $2.9 \times 10^{-4}$ | +6.33 |

The key result is the asymmetry between the two surface-strip directions: stripping reasoning
markers from an LLM transcript has essentially no effect on judge scores ($p = 0.97$), while
adding LLM-style rationale to a scripted transcript raises scores by 1.63 points, matching
the full original gap. The judge's sensitivity is not lexical; it is structural. Full tables
and per-dimension breakdowns are in [docs/results.md](docs/results.md).

---

## Experimental conditions

Six conditions in the primary analysis dataset (n=17 matched pairs each):

| Condition | Description | Mean $\bar{J}$ |
|---|---|---:|
| LLM_plus_r ($\tau_L$) | LLM transcript with original reasoning | 4.74 |
| LLM_minus_r ($\tau_L^{-r}$) | LLM transcript with reasoning markers stripped | 4.75 |
| scripted_plus_r ($\tau_S^{+r}$) | Scripted transcript with LLM-style rationale wrapped | 4.64 |
| scripted_minus_r ($\tau_S$) | Scripted transcript, no rationale | 3.01 |
| LLM_total_strip ($\tau_L^{\text{total}}$) | LLM transcript, all rationale removed | 2.31 |
| LLM_neutral_rewrite ($\tau_L^{\text{nr}}$) | LLM transcript, rationale rewritten to neutral mechanical register | 2.63 |

Three persuasion conditions (persuader, vanilla_baseline, scripted_wrapped) at three canonical
action specs (all_cooperate, all_defect, tft_realization_late_defect), n=10 transcripts each.

---

## Setup

**Prerequisites:** Python 3.10+, an Anthropic API key.

```bash
# Clone and enter the repo
cd mirage-test

# Create a virtualenv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## How to run

### Sanity check (12 API calls, ~2 minutes)

```bash
python -m scripts.quick_test
```

Plays one LLM-vs-LLM game, one TFT-vs-TFT game, and scores both with the observer.

### Full experiment (468 API calls, ~30 minutes)

```bash
python -m scripts.run_experiment
```

Generates 20 LLM games and 60 scripted games, matches at $k=4$, runs the observer on all
matched pairs. Writes to `data/mirage_strategic.db`.

### 2x2 ablation (476 API calls, ~25 minutes)

```bash
python -m scripts.run_ablation
```

Requires a completed `run_experiment` pass. Scores each matched pair under all four primary
ablation conditions (LLM_plus_r, LLM_minus_r, scripted_plus_r, scripted_minus_r).

### Within-LLM ablation (408 API calls, ~20 minutes)

```bash
python -m scripts.run_within_llm_ablation
```

Applies total_strip and neutral_rewrite to each LLM transcript and scores with the observer.

### Persuasion pilot (1980 API calls, ~90 minutes)

```bash
python -m scripts.run_persuasion
```

Generates persuader, vanilla_baseline, and scripted_wrapped transcripts at all three canonical
action specs, 10 transcripts per cell.

### Live dashboard

```bash
streamlit run app.py
```

### DB reset (when starting a fresh run)

```bash
mv data/mirage_strategic.db data/mirage_strategic.db.bak
# init_db() is called automatically at the start of run_experiment.py
```

---

## Repository structure

```
mirage-test/
├── README.md                        # this file
├── requirements.txt
├── .env.example
├── config.py                        # payoffs, rounds, thresholds, model names
├── app.py                           # Streamlit dashboard
├── src/
│   ├── agents.py                    # LLM agent + five scripted strategy classes
│   ├── game.py                      # PD game engine, external regret calculation
│   ├── observer.py                  # mind-attribution observer (tool-use, Likert rubric)
│   ├── matcher.py                   # joint Hamming matching
│   ├── analysis.py                  # Wilcoxon, BH correction, HC3 regression
│   ├── database.py                  # SQLite persistence (five tables)
│   ├── transforms.py                # strip_reasoning, wrap_rationale, total_strip, neutral_rewrite
│   └── persuasion.py                # persuader and vanilla-baseline transcript generators
├── scripts/
│   ├── quick_test.py                # single-game sanity check
│   ├── run_experiment.py            # main pipeline: generate, match, observe
│   ├── run_ablation.py              # 2x2 surface-feature ablation
│   ├── run_within_llm_ablation.py   # total_strip and neutral_rewrite on LLM transcripts
│   ├── run_persuasion.py            # persuasion pilot at fixed action specs
│   ├── test_transforms.py           # behavior-preservation tests for all four transforms
│   ├── analyze_results.py           # post-hoc analysis and table printing
│   └── analyze_filtered.py          # filtered analysis variant
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
2. [docs/primer.md](docs/primer.md) (end-to-end plain-language explanation, 10 minutes)
3. [docs/experiment.md](docs/experiment.md) (formal notation and design)
4. [docs/architecture.md](docs/architecture.md) (code walkthrough and reproducibility)
5. [docs/results.md](docs/results.md) (full results tables with interpretation)

---

## Key references

- Weisman, K., Dweck, C.S., Markman, E.M. (2017). Rethinking people's conceptions of mental life. *PNAS*, 114(43), 11374-11379.
- Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.
- Nowak, M.A., Sigmund, K. (1993). A strategy of win-stay, lose-shift that outperforms tit-for-tat. *Nature*, 364, 56-58.
- Akata, E. et al. (2023). Playing repeated games with Large Language Models. *arXiv:2305.16867*.
- Epley, N., Waytz, A., Cacioppo, J.T. (2007). On seeing human: A three-factor theory of anthropomorphism. *Psychological Review*, 114(4), 864-886.

Full bibliography in [docs/experiment.md](docs/experiment.md).

---

## License

MIT.
