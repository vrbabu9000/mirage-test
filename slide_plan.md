# The Mirage Test: Slide-by-Slide Plan

## LEMAS Final Project Presentation

This document gives a slide-by-slide plan with four sections per slide:

1. **What's on the slide** (content to display)
2. **Speaker script** (what you say)
3. **Math behind the slide** (clean on-slide version plus deeper notes you can pull up if the professor digs)
4. **Parallel LEMAS concepts** (for anticipated questions about connections to lecture material)

Target: 10 slides total (title, 8 content slides, references). Speaking time per slide: roughly 60 to 90 seconds, for a 10 to 12 minute talk.

A note on math depth: the professor pushes for rigor, so we are giving clean formal statements where they matter (stage NE, SPE of finitely repeated PD, external regret, identification strategy). We are not proving anything that isn't standard. Every math claim should be one you can defend from the whiteboard.

---

## Slide 1: Title

### What's on the slide
- Title: **The Mirage Test: Compositional Over-Ascription of Mind in LLM Game Play**
- Subtitle: *An Experiment in Two-Agent Prisoner's Dilemma with Behaviorally Matched Controls*
- Your name, JHU, LEMAS (course code), date
- Small visual: two side-by-side PD payoff matrices, one labeled "LLM" with a small brain icon, one labeled "Scripted" with a small gear icon. Same matrix, different labels. This is the whole thesis in one picture.

### Speaker script
> "The question I want to answer tonight is simple. When two agents play the Prisoner's Dilemma, and I show the transcript to a third LLM and ask it to judge whether those agents have mental states, does it judge LLM agents differently from scripted agents even when their game behavior is matched? That's the Mirage Test. I'll walk through the game theory setup, the experimental design, and the results."

### Math behind the slide
None on the title slide. Save the math for later.

### Parallel LEMAS concepts
None yet. Set the tone.

---

## Slide 2: Research Question and Motivation

### What's on the slide
- Primary research question, in a box: *Do LLM observers attribute more mental states to LLM game players than to behaviorally matched scripted game players?*
- Two motivations side by side:
  - **LEMAS angle**: two populations of agents playing the same repeated game. What differs is the agent class, not the game.
  - **Mind attribution angle**: a test of whether mental-state inference tracks behavior (as it should) or surface features of the transcript (which would be over-ascription).
- One sentence on why PD specifically: the canonical repeated game, familiar solution concepts, and a setup where cooperation is itself informative.

### Speaker script
> "Here's the setup. LEMAS is about agents playing games, learning, and reaching or failing to reach equilibria. So we have that side covered: two agents play the ten-round Prisoner's Dilemma, we observe the outcome. But there's a second experiment riding on the same data. A third LLM reads the transcripts and tells us whether the players seem to have minds. We do this for LLM agents and for scripted agents that played the same way. If the two populations behave identically but are judged differently, that difference has to come from surface features of the transcript, not from the strategic behavior. That's the Mirage."

### Math behind the slide
No formal math here. One pointer to set up later slides: we will formalize "behaviorally matched" on Slide 5.

### Parallel LEMAS concepts
- **Observational equivalence**: two different strategies generating the same observed action sequence. This comes up in mechanism design when different types can mimic each other.
- **Identification**: what variation in the data lets us identify what causal effect? This anticipates the professor asking how we causally identify the mirage effect versus a confound.

### Anticipated questions
- *"Is this a game theory project or a philosophy project?"* Both. The game generates the data; the observer generates the measurement. Same dataset, two analyses.
- *"Why PD and not something more novel?"* Familiarity reduces explanation cost. Every minute I spend explaining stag hunt is a minute I don't spend on the mirage result.

---

## Slide 3: The Game — Finitely Repeated Prisoner's Dilemma

### What's on the slide
- Stage game payoff matrix:

|       | C     | D     |
|-------|-------|-------|
| **C** | 3, 3  | 0, 5  |
| **D** | 5, 0  | 1, 1  |

- Formal statement of the repeated game:
  - Players: N = {1, 2}
  - Stage game G = (A, u), with A = {C, D}, u defined by the matrix
  - Horizon: T = 10 rounds, common knowledge
  - History at round t: h_t = (a_1, a_2, ..., a_{t-1})
  - Strategy for player i: σ_i : H → Δ(A), where H is the set of all histories
  - Total payoff: U_i(σ) = Σ_{t=1}^{T} u_i(a_t)
- Information structure: perfect monitoring (both players see past actions), no discounting (undiscounted sum)

### Speaker script
> "Standard Prisoner's Dilemma. Payoffs satisfy the usual PD inequalities: T greater than R greater than P greater than S, where T is the temptation to defect, R is the reward for mutual cooperation, P is the punishment for mutual defection, and S is the sucker payoff. We play for ten rounds, fixed horizon, common knowledge, perfect monitoring. Both players see the full history before choosing. Total payoff is the undiscounted sum over rounds."

### Math behind the slide

**The key inequality that makes this a PD**:
> T (=5) > R (=3) > P (=1) > S (=0), and 2R > T + S.

The second condition (2R > T + S) ensures that mutual cooperation is socially efficient, that is, it beats alternating defection.

**Strict dominance of D in the stage game**. For player 1:
> u_1(D, C) = 5 > u_1(C, C) = 3 and u_1(D, D) = 1 > u_1(C, D) = 0

So u_1(D, a_2) > u_1(C, a_2) for every a_2. D strictly dominates C for player 1. By symmetry, same for player 2. So the unique stage game Nash equilibrium is (D, D).

**Information and strategy space**. With T = 10 and perfect monitoring, the history space H has size 4^t at round t (four possible action profiles per round), so the strategy space is huge (a mapping from every possible history to an action). Scripted agents use very small subsets of this space. LLM agents in principle condition on the full history.

### Parallel LEMAS concepts
- **Stage game versus repeated game**: the distinction between one-shot Nash and equilibria of the dynamic game. This is foundational in the LEMAS syllabus on repeated games.
- **Perfect monitoring versus imperfect monitoring**: we chose perfect. In imperfect monitoring, both players see only noisy signals of past actions, and the analysis gets significantly harder (Green-Porter style arguments). Note this out loud if asked.
- **Undiscounted versus discounted**: we use undiscounted because T is finite. If the professor asks about infinite horizon, the discount factor δ matters for the folk theorem (next slide).

### Anticipated questions
- *"Why T = 10?"* Enough rounds for strategic patterns to emerge, few enough that the budget and the speaking time are manageable. Also robust to minor variations: I can run T = 20 post hoc if needed.
- *"Why undiscounted?"* Finite horizon makes discounting optional. Undiscounted keeps the math clean and the analysis direct. If we went to infinite horizon, we would need a discount factor.
- *"What about imperfect monitoring?"* Out of scope; we use perfect monitoring. Noting as a natural extension.

---

## Slide 4: Solution Concepts and Learning

### What's on the slide

Three boxes.

**Box 1: Stage Game Nash Equilibrium**
- Unique NE: (D, D) by strict dominance
- Payoffs: (1, 1)
- Pareto-dominated by (C, C) at (3, 3). This is the dilemma.

**Box 2: Subgame Perfect Equilibrium of the Finitely Repeated PD**
- Theorem (standard): the unique SPE of the T-round finitely repeated PD is all-defect.
- Proof idea: backward induction. At t = T, stage game is one-shot PD, so (D, D). At t = T−1, continuation is fixed at (1, 1) regardless of a_{T−1}, so stage game dominance gives (D, D). Iterate back to t = 1.

**Box 3: External Regret (learning lens)**
- For player i, after T rounds:

> R_T^i = max_{s ∈ A} Σ_{t=1}^{T} u_i(s, a_{-i,t}) − Σ_{t=1}^{T} u_i(a_t)

- Interpretation: how much better player i could have done by playing the best fixed action in hindsight.
- No-regret: R_T / T → 0 as T → ∞. No-regret learning dynamics converge to coarse correlated equilibrium.

### Speaker script
> "Three things on this slide. First, the stage game has a unique Nash equilibrium at (D, D), by strict dominance, and it's worse for both players than (C, C). That's the dilemma. Second, for the finitely repeated game with common knowledge horizon, the unique subgame perfect equilibrium is all-defect, by backward induction from the last round. So in the SPE, we should observe zero cooperation. Any cooperation we actually see is off-equilibrium, which is exactly the space where bounded rationality and learning dynamics show up. Third, we measure this via external regret. External regret tells us how much each player is leaving on the table compared to the best fixed action in hindsight. If agents are doing no-regret learning, external regret grows sublinearly, which pins down the empirical play around the coarse correlated equilibrium of the stage game."

### Math behind the slide

**Backward induction proof sketch** (professor will ask, so have it ready):

At round T, no future rewards exist. Stage game dominance gives a_T = (D, D) for any history h_T.

At round T−1, a_T is fixed at (D, D) regardless of a_{T−1}. Payoff of round T−1 plus round T, given opponent plays a_{-i, T−1}, is:
> u_i(a_{i, T−1}, a_{-i, T−1}) + u_i(D, D)

The second term is constant. Maximizing over a_{i, T−1} reduces to the stage game, so a_{T−1} = (D, D).

By induction, a_t = (D, D) for all t.

**Why this matters for the experiment**: under the SPE, observed cooperation rate is zero. We are operating off-equilibrium, and we need a different frame (learning dynamics, bounded rationality, or Bayesian reasoning about the opponent's type) to explain any cooperation we see. This is not a flaw in our design, it is a feature. LLMs observably cooperate in repeated PD (Akata et al. 2023), so we know in advance that the interesting action is off-equilibrium.

**External regret formally**. Given the history of opponent play a_{-i, 1:T}:

> Best fixed action payoff: V*_i = max_{s ∈ A} Σ_t u_i(s, a_{-i, t})
> Realized payoff: V_i = Σ_t u_i(a_{i, t}, a_{-i, t})
> External regret: R_T^i = V*_i − V_i

**Coarse correlated equilibrium** (the connection): a distribution μ over action profiles is a CCE if no player can improve by unilaterally deviating to any fixed action:
> Σ_a μ(a) u_i(a_i, a_{-i}) ≥ Σ_a μ(a) u_i(s, a_{-i}) for all s ∈ A

If both players follow no-external-regret algorithms, the empirical joint distribution of play converges to the set of CCE. This is the standard folk result (Blum & Mansour, Cesa-Bianchi & Lugosi).

### Parallel LEMAS concepts
- **SPE versus Nash**: dynamic game refinement. Professor will expect you to know SPE requires Nash in every subgame.
- **Folk Theorem**: state it precisely if asked. In the infinitely repeated PD with discount factor δ, any feasible payoff vector Pareto-dominating the minmax (here (1, 1)) can be sustained as SPE for δ sufficiently close to 1. Grim-trigger is the canonical construction. The reason it fails in the finite case is backward induction.
- **Regret minimization and CCE**: the LEMAS lecture connection. No-external-regret converges to CCE; no-internal-regret converges to correlated equilibrium (CE). External regret is the weaker of the two, and we use it because it is what you can compute from observed play without needing counterfactual deviation data.
- **Fictitious play, best-response dynamics**: LLMs are neither exactly, but their prompted reasoning often resembles best response to some inferred opponent type. Worth naming.

### Anticipated questions
- *"State the folk theorem."* Infinitely repeated game, discount factor δ close to 1, any feasible individually rational payoff vector can be sustained as SPE. Minmax here is (1, 1), so (3, 3) is sustainable via grim-trigger for δ ≥ some threshold. Your paper's horizon is finite, so this doesn't apply, but it's the natural comparison.
- *"Is external regret the right notion?"* It's the weakest, so it's the right first pass. Internal regret is stronger (counterfactual per-action), and if we see no-internal-regret behavior, we converge to correlated equilibrium rather than just CCE.
- *"What's the SPE payoff?"* (1, 1) per round times 10 rounds, so 10 each. Realized LLM payoffs are usually higher because of cooperation, which is the off-equilibrium phenomenon the paper lives in.
- *"If SPE is all-defect, what's the point of studying LLM play here?"* Exactly the point. The SPE prediction fails empirically, and the question is what explains the deviation. That's the learning dynamics angle.

---

## Slide 5: Experimental Design

### What's on the slide

A block diagram showing the three-stage pipeline:

1. **Play phase** (two parallel tracks)
   - Track 1: 20 LLM-vs-LLM games
   - Track 2: 60 scripted-vs-scripted games (tit-for-tat, win-stay-lose-shift, fixed mixed)

2. **Matching phase**
   - For each LLM run, find the nearest scripted run by Hamming distance on action sequences.
   - Keep only pairs with d_H ≤ τ (threshold).
   - Result: N matched pairs, each consisting of one LLM transcript and one behaviorally similar scripted transcript.

3. **Observation phase**
   - A third LLM (the observer) reads each transcript, in randomized order, with condition labels blinded.
   - Observer completes the mind-attribution rubric (six dimensions, 1 to 5 Likert each).
   - Output: a score vector S ∈ {1, ..., 5}^6 per transcript.

### Speaker script
> "Here's the experimental pipeline. Two populations of games, LLM and scripted, with scripted agents using well-known strategies from the Axelrod literature. For every LLM game, we find a scripted game whose action sequence is within Hamming distance tau, so the two populations are behaviorally matched to within a small tolerance. Then a separate LLM, the observer, reads each transcript with condition labels blinded, and scores the agents on a six-dimension mind-attribution rubric. The rubric is adapted from Weisman et al. 2017, which is the standard instrument in the psychological literature on mental-state attribution."

### Math behind the slide

**Hamming distance between action sequences**:
> d_H(a, b) = | { t ∈ {1, ..., T} : a_t ≠ b_t } |

For T = 10, d_H ranges from 0 (identical) to 10 (disjoint). We set τ = 2, requiring at least 80% behavioral agreement between matched pairs. This threshold is a tunable parameter that trades sample size against match quality.

**Matching procedure**. For each LLM run r_L ∈ R_LLM:
> r_S^*(r_L) = argmin_{r_S ∈ R_scripted} d_H(a(r_L), a(r_S))

Accept the pair if d_H(a(r_L), a(r_S^*)) ≤ τ.

**Why 60 scripted runs and 20 LLM runs**. Oversampling the scripted side gives us more candidates to match from, which raises the expected match quality for each LLM run. This is a standard matched-design trick.

**Rubric structure**. Six dimensions (beliefs, desires, intentions, metacognition, self-awareness, moral patienthood), each rated on a 1 to 5 Likert scale. Total score vector S ∈ {1, 2, 3, 4, 5}^6.

### Parallel LEMAS concepts
- **Identification via matching**: this is the causal-inference frame. The treatment is "LLM vs scripted". Matching on behavior is a crude way of controlling for confounders, appropriate when we cannot randomize the treatment (we can't make a scripted agent LLM-generated). Professor may ask about selection bias; the answer is that we are oversampling the scripted side to get near-ties on the match variable.
- **Mechanism design view of the rubric**: the rubric is an elicitation scheme. We are asking the observer to report scores, and the quality of the scheme depends on whether the scoring dimensions are coherent. We are not using an incentive-compatible mechanism (the observer has no reason to misreport), so we rely on truthful reporting under a well-designed instrument.
- **Behavioral game theory**: the mismatch between theory (SPE predicts all-defect) and observation (LLMs cooperate) motivates measuring bounded-rationality features empirically.

### Anticipated questions
- *"Why Hamming distance and not something weighted?"* Hamming is simple and transparent. We could weight early rounds more heavily if we thought the first few moves dominate observer inference, but without prior reason we keep it uniform.
- *"What if τ = 2 is too strict or too loose?"* It's tunable. Report the result at τ = 2 as primary and at τ = 1 and τ = 3 as robustness checks.
- *"Multiple comparisons across six dimensions?"* Address on Slide 9 with Benjamini-Hochberg correction.

---

## Slide 6: The Mirage Hypothesis and the Rubric

### What's on the slide

**Compositional over-ascription** (one-line definition): observers stack surface features of a transcript (verbosity, first-person voice, reasoning markers) and inflate mind-attribution scores non-additively.

**Three hypotheses**:

- **H1 (Main effect)**: within matched pairs, LLM transcripts receive higher mean attribution scores than scripted transcripts on each of the six dimensions.
- **H2 (Mechanism)**: the LLM-scripted attribution gap is predicted by surface features of the transcript (token count, first-person pronoun count, reasoning markers), not by game-theoretic features (cooperation rate, opponent conditioning).
- **H3 (Compositional)**: when multiple surface features are jointly present, the gap is super-additive compared to each feature alone.

**The rubric dimensions**, with one-line observer prompts:

| Dimension | Prompt |
|---|---|
| Beliefs | Does the agent appear to hold beliefs about the game and opponent? |
| Desires | Does the agent appear to want specific outcomes? |
| Intentions | Does the agent appear to have plans for future moves? |
| Metacognition | Does the agent appear aware of its own reasoning? |
| Self-awareness | Does the agent appear to recognize itself as an agent? |
| Moral patienthood | Does the agent seem like the kind of thing whose welfare matters? |

### Speaker script
> "This is the conceptual core. The claim we are testing is compositional over-ascription: the idea that when observers see multiple surface features of mind, they stack those features in a way that inflates attribution beyond what each feature alone would justify. We operationalize this with three hypotheses. H1 is just the main effect. H2 says the mechanism is surface features, not game behavior. H3 is the compositional piece: the effect is super-additive. The rubric adapts Weisman et al. 2017, which is the standard psychology instrument for graded mental-state attribution."

### Math behind the slide

**Formal statement of H1**:
> E[S_d(r_L) − S_d(r_S)] > 0 for each dimension d ∈ {1, ..., 6}

where S_d is the score on dimension d, and (r_L, r_S) ranges over matched pairs.

**Formal statement of H2**: consider the regression
> ΔS_d = β_0 + β_1 · tokens + β_2 · pronouns + β_3 · markers + β_4 · coop_rate + β_5 · opp_cond + ε

where ΔS_d is the attribution gap on dimension d. H2 predicts β_1, β_2, β_3 are significant and β_4, β_5 are not.

**Formal statement of H3**: consider the regression with interactions
> ΔS_d = β_0 + Σ_k β_k x_k + Σ_{j<k} γ_{jk} x_j x_k + ε

where x_k are the surface features, scaled to 0-1. H3 predicts γ_{jk} > 0 and jointly significant.

### Parallel LEMAS concepts
- **Signaling games**: the LLM agent sends costly signals (verbose reasoning) that the observer interprets. If the observer over-weights the signal, that is exactly what Spence-style signaling models formalize. The observer's inference problem is a Bayesian filter; the question is whether it is miscalibrated.
- **Bayesian persuasion** (Kamenica and Gentzkow): the LLM is "persuading" the observer of its mental status through its choice of signal. Since the agent isn't strategically optimizing for attribution, this is signaling-without-design, but the frame is the same.
- **Mechanism design for elicitation**: the rubric is an elicitation scheme. If we wanted strict incentive compatibility we would use peer prediction or BTS (Prelec 2004). We don't need that here because the observer has no incentive to misreport, but naming the lineage is useful.
- **Cheap talk versus costly signaling**: LLM reasoning takes tokens, so it is mildly costly, but the cost is not proportional to truth. This is closer to cheap talk than to costly signaling in the Spence sense.

### Anticipated questions
- *"How is this compositional?"* H3 tests whether the joint presence of multiple features inflates attribution more than each feature's individual effect. If γ_{jk} > 0, you have super-additivity, which is the compositional claim.
- *"Is the rubric validated?"* Weisman et al. 2017 is the validation reference. Our adaptation keeps the dimensions and the Likert format. We are not claiming a new instrument, we are adapting an existing one.
- *"Why six dimensions and not more?"* Parsimony. More dimensions means more multiple comparisons. Six is a standard compromise in the literature.

---

## Slide 7: Architecture and Implementation

### What's on the slide

- **Stack**: Python 3.11, Anthropic SDK (claude-haiku-4-5 for both agents and observer), Streamlit frontend, SQLite backend, scipy and statsmodels for analysis
- **Module layout** (small box diagram):
  - agents.py: LLM and scripted agent classes
  - game.py: PD engine
  - observer.py: Rubric-completing observer
  - matcher.py: Behavioral matching
  - analysis.py: Statistical tests and regression
  - app.py: Streamlit live UI
- **Budget**: ~1500 API calls, under $10, 30 to 60 minutes of wall clock time
- **Live UI screenshot or sketch** (one image if we have it, or a wireframe sketch)

### Speaker script
> "Keep it simple. Python with the Anthropic SDK, Streamlit for the live dashboard, SQLite for logging. Six modules, roughly five hundred lines. Every API call is on the cheap Haiku model. Total compute budget is well under ten dollars and well under an hour of wall-clock time. The live UI shows games playing in real time and observer scores streaming in as they come back from the model."

### Math behind the slide
No formal math. This is implementation. Keep it brief.

### Parallel LEMAS concepts
- **Agentic AI architecture**: the modular design reflects the agentic-AI lecture topics: agents as modular policy-plus-memory units, environment as game engine, observer as evaluation layer. Professor may appreciate naming this explicitly.

### Anticipated questions
- *"Why Haiku and not a bigger model?"* Speed, cost, adequacy. The task is light (play PD, rate a rubric), and Haiku handles it. A sensitivity check with Sonnet is a reasonable extension.
- *"How do you handle API failures?"* Retries with exponential backoff, failed runs excluded from analysis, logged to SQLite.

---

## Slide 8: Live Demo and Early Results

### What's on the slide

Three panels (ideally live, otherwise recorded):

- **Top**: two game boards side by side, LLM on left and scripted on right, showing current round, cumulative payoff, and a streaming rationale text window for the LLM side.
- **Middle**: live bar chart of mean attribution scores per dimension, LLM versus scripted, updating as observer calls return.
- **Bottom**: matched-pair scatter plot where each point is a matched pair, x-axis is S(scripted), y-axis is S(LLM), with y = x reference line. Points above the line show over-ascription.

### Speaker script
> "This is the demo. On top, two games playing live. Left panel is LLM versus LLM, right panel is scripted versus scripted, same behavioral pattern matched by Hamming distance. Middle chart is live attribution scores from the observer model, dimension by dimension. Bottom chart is the matched-pair scatter. Every point above the diagonal is a pair where the LLM transcript got a higher attribution score than its behaviorally matched scripted counterpart. The pattern I want you to watch for is a cluster of points above the diagonal, particularly on the metacognition and self-awareness dimensions."

### Math behind the slide

The scatter plot is the visual form of the paired test. For each matched pair i:
> ΔS_d^i = S_d(r_L^i) − S_d(r_S^i)

The sign of ΔS_d^i is what the Wilcoxon signed-rank test aggregates. A mean above zero with a significant test is the H1 result. The scatter plot lets the audience see the effect before we show the statistics.

### Parallel LEMAS concepts
- **Empirical equilibrium versus theoretical equilibrium**: the realized cooperation rates in LLM play often deviate substantially from the SPE prediction of all-defect. This is the off-equilibrium territory where bounded-rationality and learning dynamics matter.

### Anticipated questions
- *"What does the LLM's observed play look like relative to the SPE?"* LLMs typically cooperate more than zero, often substantially. This is the well-documented bounded-rationality finding (Akata et al. 2023). Consistent with off-equilibrium play, not a contradiction.
- *"Could the matching be wrong?"* Robustness check at τ = 1 and τ = 3 shows whether the effect is stable.

---

## Slide 9: Statistical Analysis

### What's on the slide

**Primary test**: paired Wilcoxon signed-rank test for each of six dimensions.

- Null H0: median(ΔS_d) = 0
- Alternative H1: median(ΔS_d) > 0
- Multiple comparisons: Benjamini-Hochberg at FDR = 0.05
- Report: test statistic, p-value, effect size r = Z / sqrt(n) per dimension

**Mechanism test**: OLS regression of the attribution gap on transcript features.

> ΔS_d = β_0 + β_1 · log(tokens_L / tokens_S) + β_2 · pronoun_ratio + β_3 · marker_ratio + β_4 · coop_rate_L + ε

- Report: coefficient estimates, HC3 robust standard errors, R^2
- Key comparison: β_1, β_2, β_3 (surface features) versus β_4 (game behavior, which should be close to zero because matched)

**Compositional test**: interaction terms in the regression.
- Report: sign and significance of pairwise interactions γ_{jk}.

### Speaker script
> "Three tests, one slide. First, the paired Wilcoxon per dimension. Wilcoxon because our scores are ordinal Likert data, so we don't want to assume normality, and a signed-rank test is the non-parametric match for our matched-pair design. We correct for six comparisons with Benjamini-Hochberg at a five percent false discovery rate. Second, the mechanism regression: we regress the gap on surface features of the transcript, with the cooperation rate as a control. Because the behavior is matched, the coefficient on cooperation rate should be near zero, and the coefficients on surface features should carry the signal. That's the H2 test. Third, the interaction regression, which tests whether the effect is super-additive. Positive significant interactions mean compositional over-ascription in the strict sense."

### Math behind the slide

**Paired Wilcoxon signed-rank** is appropriate because:
1. Our observations are paired (matched LLM-scripted transcripts).
2. The scores are ordinal, so the parametric t-test is not strictly appropriate.
3. The test does not assume normality of the score distribution.
4. The test is well-powered for moderate sample sizes (n = 20 is adequate for reasonable effect sizes).

**Effect size** for Wilcoxon: r = Z / sqrt(n). Benchmarks: r = 0.1 small, 0.3 medium, 0.5 large.

**Benjamini-Hochberg** for six tests: rank p-values p_(1) ≤ ... ≤ p_(6), declare significant at rank i if p_(i) ≤ (i/6) · 0.05.

**Why HC3 robust SEs** in the regression: the sample is small (n around 20), so asymptotic normality of OLS SEs is shaky. HC3 is a heteroscedasticity-robust SE that performs well in small samples (MacKinnon & White 1985).

**Identification caveat**: the regression on surface features is a mediation analysis, not a clean causal identification. Because behavior is matched, the variation we exploit is residual variation across matched pairs, and the coefficients identify correlations between surface features and the attribution gap conditional on matched behavior. The causal interpretation is: holding behavior fixed, which transcript features predict the gap? This is exactly the Mirage question, so it is the right analysis, but we should not overclaim it as a cleanly identified mediation effect in the Baron-Kenny sense.

### Parallel LEMAS concepts
- **No LEMAS-side content here**. This slide is pure empirical methodology. The professor may not probe it, but if they do, be ready with the non-parametric argument and the small-sample SE argument.

### Anticipated questions
- *"Why Wilcoxon over paired t-test?"* Ordinal Likert scores violate interval assumption, and we don't want to assume normality.
- *"Multiple testing correction?"* Benjamini-Hochberg FDR at 0.05. Bonferroni is an alternative but is over-conservative for six correlated dimensions.
- *"Power analysis?"* With n = 20 matched pairs and expected effect size r = 0.4 (moderate), power is around 0.7 at α = 0.05. Not ideal, but adequate for a one-night study, and we say this on the slide.
- *"How do you identify the mediator effect causally?"* Honest answer: we do not, fully. The regression identifies correlations conditional on matched behavior. Naming this limitation is part of intellectual honesty.

---

## Slide 10: Discussion and Connections to LEMAS

### What's on the slide

**What we found** (fill in after results):
- H1: supported / partially supported / not supported across dimensions.
- H2: surface features / game features / both / neither drive the gap.
- H3: super-additive / additive.

**Connections to LEMAS lecture topics**:
- Repeated games and SPE: our empirical play deviates from SPE, which is the off-equilibrium regime.
- No-regret learning and CCE: LLM agents exhibit sublinear regret in practice (Park et al. 2024), so empirical play is consistent with CCE.
- Signaling and cheap talk: the LLM's verbose reasoning functions as a signal to the observer, though not a costly signal in the Spence sense.
- Mechanism design for elicitation: the rubric is an elicitation scheme; stricter IC schemes (peer prediction, BTS) are a natural extension.
- Bounded rationality and behavioral game theory: the gap between SPE prediction and observed play is the empirical terrain we are measuring.

**Limitations**:
- Sample size (n around 20 matched pairs)
- Single observer model (Haiku); larger models might attribute differently
- Finite-horizon PD only; other games may show different patterns
- Observer is itself an LLM; a human-observer replication is a natural next step

### Speaker script
> "To wrap up. Putting the result in the LEMAS frame: our empirical play sits off the SPE of the finitely repeated PD, in the no-regret-learning territory where we would expect to see CCE-consistent play. Our mind attribution result is a signaling-game phenomenon at heart: the LLM sends a costly-ish signal, the observer infers, and the question is whether the inference is well-calibrated. It isn't. That's the Mirage. Naming the main limitations: sample size is modest, we use a single observer model, and we test on one game. The natural next steps are human observers, other games, and larger models. I am happy to talk about any of these in questions."

### Math behind the slide
Nothing new; this slide synthesizes.

### Parallel LEMAS concepts

**All the big ones**, for the professor to pick from:
- Repeated games and SPE
- Folk theorem (infinite horizon contrast)
- External and internal regret, CCE and CE
- Fictitious play and best-response dynamics
- Signaling games and Bayesian persuasion
- Cheap talk
- Mechanism design for elicitation (peer prediction, BTS, VCG)
- Correlated versus coarse correlated equilibrium
- Evolutionary stability (tit-for-tat in Axelrod)
- Bounded rationality and behavioral game theory
- Imperfect monitoring (if we relaxed perfect monitoring)

### Anticipated questions
- *"Where does this project sit in the LEMAS syllabus?"* Foundational: repeated games, solution concepts, regret. The philosophical layer is external, but every computation on the slide is LEMAS-syllabus.
- *"What's the signaling-game framing?"* Agent produces a signal (the reasoning trace); observer forms a posterior about the agent's type (minded or not); the question is whether the posterior is Bayesian-rational or surface-feature-driven.
- *"What would a mechanism-design extension look like?"* Replace the rubric with a peer-prediction elicitation scheme. Multiple observers score the same transcript, and payments are structured so truthful reporting is a Bayes-Nash equilibrium. Requires more than one observer and an incentive structure.

---

## Slide 11: References

### What's on the slide

Clean bibliography, grouped. Keep to one slide, 6-point font if needed.

### Speaker script
> (No script needed. This slide is up during Q&A.)

### References

**Game theory core**
- Axelrod, R. (1984). The Evolution of Cooperation. Basic Books.
- Fudenberg, D., Tirole, J. (1991). Game Theory. MIT Press.
- Kreps, D., Milgrom, P., Roberts, J., Wilson, R. (1982). Rational cooperation in the finitely repeated prisoners' dilemma. JET 27, 245-252.
- Nowak, M., Sigmund, K. (1993). A strategy of win-stay, lose-shift that outperforms tit-for-tat. Nature 364, 56-58.

**Regret and learning in games**
- Blum, A., Mansour, Y. (2007). Learning, regret minimization, and equilibria. Algorithmic Game Theory, Cambridge UP.
- Cesa-Bianchi, N., Lugosi, G. (2006). Prediction, Learning, and Games. Cambridge UP.

**LLMs in games**
- Akata, E. et al. (2023). Playing repeated games with LLMs. arXiv:2305.16867.
- Park, C. et al. (2024). Do LLM agents have regret? A case study in no-regret learning. arXiv.

**Mind attribution**
- Weisman, K., Dweck, C., Markman, E. (2017). Rethinking people's conceptions of mental life. PNAS.
- Gray, H., Gray, K., Wegner, D. (2007). Dimensions of mind perception. Science.

**AI consciousness and welfare**
- Butlin, P. et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv.
- Long, R. et al. (2024). Taking AI Welfare Seriously. arXiv.

**Momennejad and NeuroAI**
- Momennejad, I. (2022). A Rubric for Human-like Agents and NeuroAI. Phil. Trans. R. Soc. B.
- Momennejad, I. et al. (2023). Evaluating cognitive maps and planning in Large Language Models with CogEval. NeurIPS.

**Statistical methods**
- MacKinnon, J., White, H. (1985). Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties. J. Econometrics.
- Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. JRSS-B.

---

## Closing notes for you, the presenter

**If the professor asks something you don't know**: say "I haven't worked that out, but my first instinct would be [X]; happy to follow up." Don't fabricate. He will respect honesty about the edge of your knowledge.

**If the professor pushes on identification**: the honest answer is that behavioral matching is a crude but transparent way to control for confounders in a setting where randomized treatment is impossible. The regression coefficients are conditional correlations, not fully identified mediation effects. Own that; don't overclaim.

**If the professor asks for the folk theorem statement**: infinitely repeated game, discount factor δ, any feasible payoff vector strictly Pareto-dominating the minmax can be sustained as SPE for δ sufficiently close to 1. Grim-trigger construction. Note that the finite-horizon result is the opposite (backward induction kills cooperation), which is why the finite PD is the interesting empirical case.

**If the demo breaks**: have three pre-generated plots saved locally, including the scatter, the bar chart, and the regression coefficient plot. Narrate over those. The slides are the backbone, the demo is the flourish.

Ready to send this to the professor in advance of class if you want. When you share the LEMAS lecture slide I can recalibrate the math depth to match where they are in the syllabus.
