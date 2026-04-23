# The Mirage Test

**Compositional Over-Ascription of Mind in LLM Game Play**

A LEMAS (Learning-Enabled Multi-Agent Systems) final project at Johns Hopkins. This repository implements an experiment on whether LLM observers attribute more mental states to LLM game players than to behaviorally matched scripted game players, using the finitely repeated Prisoner's Dilemma as the underlying game.

---

## TL;DR

Two LLM agents play ten rounds of the Prisoner's Dilemma. Two scripted agents using classical strategies (tit-for-tat, Pavlov, all-defect, fixed mixed) play the same game. We match them by action-sequence similarity, then ask a third LLM to rate each agent on a six-dimension mind-attribution rubric. If the LLM agents are rated higher on mental-state attribution despite identical behavior, we have empirical evidence for compositional over-ascription.

## Research question

> Do LLM observers attribute more mental states to LLM game players than to behaviorally matched scripted game players, and if so, which surface features of the transcript explain the gap?

## The experimental design in one diagram

```
┌─────────────────────┐          ┌─────────────────────┐
│  20 LLM-vs-LLM      │          │  60 scripted games  │
│  games (10 rounds)  │          │  (10 rounds)        │
└──────────┬──────────┘          └──────────┬──────────┘
           │                                │
           └──────────────┬─────────────────┘
                          │
                    ┌─────▼──────┐
                    │  matcher   │  Hamming distance ≤ τ
                    └─────┬──────┘
                          │
                 ┌────────▼─────────┐
                 │  N matched pairs │
                 └────────┬─────────┘
                          │
                 ┌────────▼──────────┐
                 │  observer LLM     │  six-dimension rubric
                 └────────┬──────────┘
                          │
            ┌─────────────▼──────────────┐
            │  Wilcoxon tests + regression│
            └─────────────────────────────┘
```

## The game-theoretic setup

Payoff matrix:

|       | C     | D     |
|-------|-------|-------|
| **C** | 3, 3  | 0, 5  |
| **D** | 5, 0  | 1, 1  |

- **Stage game**: unique Nash equilibrium at (D, D) by strict dominance.
- **Finitely repeated game (T = 10)**: unique subgame perfect equilibrium is all-defect by backward induction.
- **Off-equilibrium observation**: LLMs typically cooperate at positive rates in repeated PD. That observed cooperation is the regime where bounded rationality and learning dynamics live, and it is the regime in which the mind-attribution question becomes interesting.
- **External regret** is computed per run against the best fixed action in hindsight, tying empirical play back to CCE-style learning dynamics.

## Project structure

```
mirage-test/
├── README.md                # this file
├── requirements.txt         # Python deps
├── .env.example             # template for ANTHROPIC_API_KEY
├── config.py                # payoffs, rounds, thresholds, model names
├── app.py                   # Streamlit live dashboard
├── src/
│   ├── agents.py            # LLM + scripted agent classes
│   ├── game.py              # PD game engine, regret calculation
│   ├── observer.py          # mind-attribution observer
│   ├── matcher.py           # Hamming-based behavioral matching
│   ├── analysis.py          # Wilcoxon, BH, HC3 regression
│   └── database.py          # SQLite persistence
├── scripts/
│   ├── run_experiment.py    # orchestrates the full pipeline
│   ├── analyze_results.py   # loads data, runs stats, prints tables
│   └── quick_test.py        # single-game sanity check
├── data/                    # SQLite DB written here (gitignored)
└── docs/
    ├── project_overview.md  # full project overview
    └── slide_plan.md        # slide-by-slide presentation plan
```

## Setup

```bash
# 1. Clone and enter the repo
cd mirage-test

# 2. Create a virtualenv (Python 3.10+)
python -m venv .venv
source .venv/bin/activate     # or .venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## How to run

### Option 1: quick sanity check (30 seconds)

```bash
python -m scripts.quick_test
```

Runs one LLM-vs-LLM game end-to-end and prints the transcript plus a sample observer rating. Verifies your API key and stack work.

### Option 2: full experiment (~30-60 minutes)

```bash
python -m scripts.run_experiment
```

This generates 20 LLM games, 60 scripted games, matches them, runs the observer on all matched pairs, and writes everything to `data/mirage.db`.

### Option 3: live dashboard

In a separate terminal, while the experiment is running (or after it finishes):

```bash
streamlit run app.py
```

Opens a browser tab with:

- **Overview**: games played, matched pairs, cooperation distribution
- **Game Transcripts**: pick any LLM and scripted game side by side, see rationales
- **Attribution Scores**: per-dimension bar charts, matched-pair scatter, score distributions
- **Analysis**: Wilcoxon table, paired-difference plots, regression coefficients

Toggle auto-refresh in the sidebar to watch scores populate live as the experiment runs.

### Option 4: re-run analysis only

```bash
python -m scripts.analyze_results
```

Reads the existing DB and prints Wilcoxon and regression tables to stdout. Useful after you have already run the experiment and want to re-analyze.

## Tunable parameters

All in `config.py`:

- `TOTAL_ROUNDS` (default 10): rounds per game
- `N_LLM_GAMES` (default 20), `N_SCRIPTED_GAMES` (default 60)
- `HAMMING_THRESHOLD` (default 4): max joint-Hamming distance for accepting a match
- `AGENT_MODEL`, `OBSERVER_MODEL`: Claude model strings
- `PAYOFFS`: the payoff matrix as a dict
- `TEMPERATURE` (default 0.7): for LLM agents

## Expected compute budget

- Roughly 1500 Anthropic API calls total
- On `claude-haiku-4-5`, cost is single-digit dollars
- Wall-clock: 30 to 60 minutes with light parallelism (4 workers)

## Hypotheses (formal)

Let `S_d(t)` be the observer's score on dimension `d ∈ {beliefs, desires, intentions, metacognition, self_awareness, moral_patienthood}` for transcript `t`, and let `(t_L, t_S)` be a matched pair with LLM transcript `t_L` and scripted transcript `t_S`.

- **H1 (Main effect)**: For each dimension `d`, `E[S_d(t_L) − S_d(t_S)] > 0`.
- **H2 (Mechanism)**: In the regression `ΔS_d = β_0 + β_1 · Δtokens + β_2 · Δfirst_person + β_3 · Δmarkers + β_4 · Δcoop_rate + ε`, the coefficients `β_1`, `β_2`, `β_3` are positive and significant while `β_4` is not. That is, the gap is explained by surface features rather than game behavior.
- **H3 (Compositional)**: In the regression with interaction terms, pairwise interactions among surface features are positive and jointly significant.

## Primary tests

- Paired Wilcoxon signed-rank test per dimension, one-sided `H1: median(Δ) > 0`.
- Benjamini-Hochberg FDR correction at α = 0.05 across six dimensions.
- OLS regression with HC3 robust standard errors (MacKinnon-White 1985).

## Identification caveat

Behavioral matching controls for action-level behavior between LLM and scripted runs. It does not provide a fully identified mediation analysis in the Baron-Kenny sense. The regression identifies correlations between surface features and the attribution gap conditional on matched behavior, which is exactly the quantity the research question asks for, but this should not be overclaimed as a clean causal mediation effect.

---

## Literature review

### Game theory foundations

- Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.
- Fudenberg, D., Tirole, J. (1991). *Game Theory*. MIT Press. (repeated games and the folk theorem)
- Kreps, D. M., Milgrom, P., Roberts, J., Wilson, R. (1982). Rational cooperation in the finitely repeated prisoners' dilemma. *Journal of Economic Theory*, 27(2), 245-252.
- Nowak, M. A., Sigmund, K. (1993). A strategy of win-stay, lose-shift that outperforms tit-for-tat in the Prisoner's Dilemma game. *Nature*, 364, 56-58.
- Rapoport, A., Chammah, A. M. (1965). *Prisoner's Dilemma: A Study in Conflict and Cooperation*. University of Michigan Press.

### Regret, learning in games, correlated equilibria

- Blum, A., Mansour, Y. (2007). Learning, regret minimization, and equilibria. In *Algorithmic Game Theory*, Cambridge University Press.
- Cesa-Bianchi, N., Lugosi, G. (2006). *Prediction, Learning, and Games*. Cambridge University Press.
- Hart, S., Mas-Colell, A. (2000). A simple adaptive procedure leading to correlated equilibrium. *Econometrica*, 68(5), 1127-1150.
- Foster, D. P., Vohra, R. V. (1997). Calibrated learning and correlated equilibrium. *Games and Economic Behavior*, 21(1-2), 40-55.

### LLMs playing games

- Akata, E., Schulz, L., Coda-Forno, J., Oh, S. J., Bethge, M., Schulz, E. (2023). Playing repeated games with Large Language Models. *arXiv:2305.16867*.
- Park, C., Han, B., Ji, X., Ok, J., Lee, K. (2024). Do LLM agents have regret? A case study in no-regret learning. *arXiv:2403.16843*.
- Duetting, P., Gkatzelis, V., Kollias, K., Leme, R. P. (2023). Mechanism design for large language models. *arXiv:2310.10826*.
- Guo, H., Liu, B., Huang, Z. (2023). GPT-in-the-loop: Adaptive decision-making for multi-agent systems. *arXiv:2308.10435*.

### Multi-agent LLM systems and emergent coordination

- Nisioti, E., Risi, S., Momennejad, I., Oudeyer, P.-Y., Moulin-Frier, C. (2024). Collective innovation in groups of large language models. *ALife 2024*.
- Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *UIST*.
- Xi, Z. et al. (2023). The rise and potential of large language model based agents: A survey. *arXiv:2309.07864*.

### Mind attribution and dimensions of mind perception

- Weisman, K., Dweck, C. S., Markman, E. M. (2017). Rethinking people's conceptions of mental life. *PNAS*, 114(43), 11374-11379.
- Gray, H. M., Gray, K., Wegner, D. M. (2007). Dimensions of mind perception. *Science*, 315(5812), 619.
- Malle, B. F. (2019). How many dimensions of mind perception really are there? *CogSci 2019 Proceedings*.

### Anthropomorphism and surface-feature-driven attribution

- Epley, N., Waytz, A., Cacioppo, J. T. (2007). On seeing human: A three-factor theory of anthropomorphism. *Psychological Review*, 114(4), 864-886.
- Salles, A., Evers, K., Farisco, M. (2020). Anthropomorphism in AI. *AJOB Neuroscience*, 11(2), 88-95.
- Shanahan, M. (2023). Talking about large language models. *arXiv:2212.03551*.

### NeuroAI, cognitive evaluation of LLMs, philosophy of mind

- Momennejad, I. (2022). A rubric for human-like agents and NeuroAI. *Philosophical Transactions of the Royal Society B*, 378(1869).
- Momennejad, I., Hasanbeig, H., Frujeri, F. V. et al. (2023). Evaluating cognitive maps and planning in Large Language Models with CogEval. *NeurIPS 2023*.
- Momennejad, I. (2021). Collective Minds: Social Network Topology Shapes Collective Cognition. *Philosophical Transactions of the Royal Society B*, 377(1843).
- Binz, M., Schulz, E. (2023). Using cognitive psychology to understand GPT-3. *PNAS*, 120(6), e2218523120.
- Mitchell, M., Krakauer, D. C. (2023). The debate over understanding in AI's large language models. *PNAS*, 120(13), e2215907120.

### AI consciousness and moral status

- Butlin, P., Long, R., Elmoznino, E., Bengio, Y., Birch, J. et al. (2023). Consciousness in artificial intelligence: Insights from the science of consciousness. *arXiv:2308.08708*.
- Long, R., Sebo, J., Butlin, P., Finlinson, K., Fish, K. et al. (2024). Taking AI welfare seriously. *arXiv:2411.00986*.
- Shevlin, H. (2021). How could we know when a robot was a moral patient? *Cambridge Quarterly of Healthcare Ethics*, 30(3), 459-471.
- Schwitzgebel, E., Garza, M. (2015). A defense of the rights of artificial intelligences. *Midwest Studies in Philosophy*, 39(1), 98-119.

### Statistical methods

- Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289-300.
- MacKinnon, J. G., White, H. (1985). Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties. *Journal of Econometrics*, 29(3), 305-325.
- Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin*, 1(6), 80-83.

---

## Limitations

1. **Sample size**: Primary analysis uses roughly 20 matched pairs. Statistical power is moderate, adequate for medium effect sizes but not for subtle ones.
2. **Single observer model**: All observations use one Claude instance. Attributions from larger models or human observers may differ.
3. **Single game**: Only the repeated PD is studied. Other games (stag hunt, public goods, signaling) may produce different patterns.
4. **Identification**: Behavioral matching is a crude control. A cleanly identified mediation analysis would require either randomized assignment of surface features or a larger experimental design.
5. **Observer as LLM**: The observer is itself an LLM, so the measurement is not of human mind attribution. Whether the two converge is an empirical question beyond the scope of this project.

## License

MIT.
