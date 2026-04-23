# The Mirage Test

## A hackathon experiment on mind attribution in LLM game play

**Course**: Learning-Enabled Multi-Agent Systems (LEMAS), Johns Hopkins
**Game**: Finitely Repeated Prisoner's Dilemma
**Scope**: One night build, live Streamlit UI, full analysis
**Secondary audience**: AI Sentience Scholars Program (AISS / Neuromatch) application

---

## TL;DR in one sentence

When an LLM observer watches two agents play the Prisoner's Dilemma, does it attribute more "mental states" to LLM agents than to scripted agents, even when those agents behave identically?

---

## Background, for someone who hasn't thought about this

When you watch something behave, you can't help forming a mental model of why it's behaving that way. If a dog approaches a treat, you think "it wants the treat." If a thermostat turns on the heat, you don't think "it wants warmth." But if the thermostat were dressed up to look like a pet, or if it produced little speech bubbles explaining its decisions ("It's cold in here, I should turn on the heat"), you might start attributing mental states to it that it doesn't really have.

Philosophers call this the problem of **mental state attribution**, and it sits at the center of a live debate about LLMs. LLMs produce fluent first-person text, offer reasoning traces, explain their decisions in natural language, and generally exhibit all the surface features that trigger mind attribution in humans. But there's no settled answer about whether they *have* mental states in any serious sense. Some researchers think the attribution is warranted. Others think LLMs are triggering a kind of cognitive illusion where a compositional stack of surface features gets read as "mind."

The **AI Sentience Scholars Program (AISS)** is a research program that takes these questions seriously. It funds and mentors work on AI consciousness, moral patienthood, metacognition, and mind attribution. The core questions are: When does an AI system count as having mental states? What would count as evidence? When are humans (or other AIs) over-attributing minds to systems that don't have them?

**Ida Momennejad**, a neuroscientist and AI researcher at Microsoft Research NYC, has argued in her recent work that a lot of the current excitement about LLM minds is a kind of "mirage". Surface features of the outputs trigger mind-attribution machinery in observers, and those features get combined (composed) in ways that inflate the attribution beyond what the underlying system warrants. Her framing is that mind attribution to LLMs is often **compositional over-ascription**: the features stack, and each new feature (reasoning trace, affective language, self-reference) nudges attribution upward more than it strictly should.

This project tests that claim directly. If LLM observers attribute more mind to LLM agents than to scripted agents when the two are *behaving the same way*, we have direct empirical evidence for the mirage thesis. If they don't, we have a negative finding that's interesting in its own right.

---

## The LEMAS side: game theory

LEMAS cares about agents playing games, with formal solution concepts and measurable outcomes. The Prisoner's Dilemma fits perfectly and everyone in the class already knows it, so there's no setup cost on the math side.

### Quick recap of the game

Two players. Each chooses Cooperate (C) or Defect (D). Payoffs are such that:

- Mutual cooperation (C, C) pays 3 to each
- Mutual defection (D, D) pays 1 to each
- One defects and one cooperates: defector gets 5, cooperator gets 0

Defection is a dominant strategy in the one-shot game. No matter what the other player does, defecting pays more. So the unique Nash equilibrium of the one-shot PD is (D, D), which is worse for both players than (C, C). This is the famous dilemma.

### Repeated PD

In the **finitely repeated PD**, the unique subgame perfect equilibrium is still all-defect by backward induction. If both players know the game will end at round T, they both defect at round T. Knowing that, they defect at T-1. And so on back to round 1.

In the **infinitely repeated PD** (or with discounting), cooperation can be sustained as an equilibrium by strategies that punish defection. The **Folk Theorem** says any feasible, individually rational payoff vector can be sustained as an equilibrium with sufficiently patient players. **Tit-for-tat** is the most famous such strategy: cooperate on round 1, then mirror whatever the other player did last round. Axelrod's 1984 tournaments showed tit-for-tat wins against a wide variety of strategies in iterated PD.

### Our game setup

Our agents play a 10-round PD. We measure:

- Cooperation rate across rounds
- Average payoff per round
- External regret against the best fixed action in hindsight
- Convergence behavior

That's our game theory slide. Clean and standard.

---

## The AISS side: mind attribution

The experimental manipulation is what makes this project different from a vanilla repeated-PD study. We run two parallel populations of games.

### Two populations

1. **LLM population**: two Claude agents play the 10-round PD. They see the history, reason freely in natural language before committing to a move, and produce verbose rationale traces.

2. **Scripted population**: two scripted agents play the same 10-round PD. They use classical strategies from the game theory literature: tit-for-tat, win-stay-lose-shift, a fixed mixed strategy. Their "reasoning" is just code.

### The critical control: behavioral matching

For each LLM run, we pair it with a scripted run whose action sequence is close. "Close" is operationalized as Hamming distance on the action sequences, or cooperation-rate match within a tolerance. This control is what makes the experiment falsifiable. Without it, any difference we find could just be a difference in how the agents play, not a difference in how they're perceived.

### The observer

A third LLM instance (the **observer**) reads each transcript and completes a structured mind-attribution rubric. The rubric is adapted from existing psychology instruments (Weisman et al. 2017 dimensions of mental life). It scores the agents on:

- **Beliefs**: does the agent seem to have beliefs about the world?
- **Desires**: does the agent seem to want things?
- **Intentions**: does the agent seem to have plans?
- **Metacognition**: does the agent seem aware of its own thinking?
- **Self-awareness**: does the agent seem aware of itself as an agent?
- **Moral patienthood**: does the agent seem like the kind of thing whose welfare matters?

Each dimension gets a 1 to 5 Likert rating.

Because transcripts are behaviorally matched, any difference in attribution scores between LLM and scripted transcripts cannot be explained by what the agents did. It must come from *how* they did it: verbosity, first-person language, reasoning traces.

That's the Mirage test.

---

## Hypotheses

- **H1 (Main effect)**: Observer LLMs rate LLM agents higher than behaviorally-matched scripted agents on mind-attribution dimensions.
- **H2 (Mechanism)**: The attribution gap is predicted by surface features of the transcript (token count, first-person pronoun count, explicit reasoning markers) rather than by anything about the actual game-theoretic behavior.
- **H3 (Compositional)**: The effect is super-additive when multiple surface features are present, not just a linear combination of each.

If H1 holds, the mirage effect is confirmed in this paradigm. If H2 holds, we have identified the mechanism. If H3 holds, that's the compositional piece of "compositional over-ascription."

---

## Architecture

Keeping it lean.

### Stack

- Python 3.11+
- Anthropic SDK, using `claude-haiku-4-5` for agents and observer (fast, cheap, adequate)
- Streamlit for the live UI (fastest path to a real-time dashboard)
- SQLite for logging every game, every decision, every observer rating
- Pandas, NumPy, SciPy for analysis
- Plotly for visualizations in the Streamlit app

### Modules

Roughly 500 lines of code total, split across six files.

1. **`agents.py`**: The LLM agent class (prompted to play PD) and the scripted agent classes (tit-for-tat, win-stay-lose-shift, fixed mixed strategy). Standard interface: given history, return action and rationale string.
2. **`game.py`**: The PD game engine. Runs N rounds of a matchup between any two agents. Logs actions, rationales, payoffs to SQLite.
3. **`observer.py`**: The LLM observer that reads a transcript and completes the attribution rubric. Returns structured JSON with scores on each dimension plus a free-text justification.
4. **`matcher.py`**: Pairs LLM runs with scripted runs by behavioral similarity (Hamming distance on action sequences).
5. **`analysis.py`**: Paired statistical tests (Wilcoxon signed-rank per dimension) and regression of attribution scores on transcript surface features (token count, first-person pronoun frequency, reasoning marker frequency).
6. **`app.py`**: The Streamlit frontend. Shows games being played live, observer scores coming in, and plots updating in real time.

### Run plan

1. Generate 20 LLM-vs-LLM runs
2. Generate 60 scripted-vs-scripted runs (so we have candidates to pair from)
3. Match each LLM run to its nearest scripted run by action sequence similarity
4. Run the observer on all 40 transcripts (20 LLM, 20 matched scripted), with condition labels blinded
5. Compute statistics, generate plots, write the slides

### Compute budget

- Roughly 1000 to 1500 API calls total, almost entirely on the cheap Haiku model
- Cost: single-digit dollars
- Wall-clock time: 30 to 60 minutes for data generation with light parallelism

### Live UI layout (Streamlit)

- **Top**: two side-by-side game panels, LLM on the left and scripted on the right, showing actions per round, cumulative payoff, rationale text streaming in
- **Middle**: a live mind-attribution bar chart that updates as observer scores come in, showing the gap per dimension
- **Bottom**: a summary plot of paired differences across dimensions with confidence intervals, and a regression coefficient plot showing which surface features predict the attribution gap

The "same behavior, different attribution" visual is the centerpiece of the presentation. It argues the paper by itself.

---

## What we expect to find

Best guess: LLM agents get higher attribution scores across most dimensions. The largest gaps land on metacognition and self-awareness, which are the dimensions where first-person reasoning language matters most. The regression will probably pick out token count and first-person pronoun frequency as the dominant predictors.

Null results are also legitimate. If LLM observers aren't fooled by surface features, that complicates the mirage thesis in a publishable way.

Either result is defensible in the room.

---

## Literature review (paper list)

### Mind attribution and dimensions of mind perception

- Weisman, Dweck, Markman (2017). "Rethinking people's conceptions of mental life." *PNAS*.
- Gray, Gray, Wegner (2007). "Dimensions of mind perception." *Science*.
- Shevlin (2021). "How could we know when a robot was a moral patient?" *Cambridge Quarterly of Healthcare Ethics*.

### Momennejad's relevant work

- Momennejad (2022). "A Rubric for Human-like Agents and NeuroAI." *Philosophical Transactions of the Royal Society B*.
- Momennejad et al. (2023). "Evaluating cognitive maps and planning in Large Language Models with CogEval." *NeurIPS*.
- Momennejad (2021). "Collective Minds: Social Network Topology Shapes Collective Cognition." *Phil. Trans. R. Soc. B*.
- Momennejad (2026, forthcoming). "The Ontological Reversal of Computation and the Brain." *Philosophy and the Mind Sciences*.

### LLMs and moral status / AI consciousness

- Butlin et al. (2023). "Consciousness in Artificial Intelligence: Insights from the Science of Consciousness." *arXiv preprint*.
- Long et al. (2024). "Taking AI Welfare Seriously." *arXiv preprint*.
- Schwitzgebel, Garza (2015). "A defense of the rights of artificial intelligences." *Midwest Studies in Philosophy*.

### Game theory foundations

- Axelrod (1984). *The Evolution of Cooperation*. Basic Books.
- Nowak, Sigmund (1993). "A strategy of win-stay, lose-shift that outperforms tit-for-tat in the Prisoner's Dilemma game." *Nature*.
- Kreps, Milgrom, Roberts, Wilson (1982). "Rational cooperation in the finitely repeated prisoners' dilemma." *Journal of Economic Theory*.
- Fudenberg, Tirole (1991). *Game Theory*. MIT Press. (reference chapters on repeated games and the folk theorem)

### LLMs in games (from our midterm survey, relevant here)

- Akata et al. (2023). "Playing repeated games with Large Language Models." *arXiv*.
- Park et al. (2024). "Do LLM agents have regret? A case study in no-regret learning." *arXiv*.

### Anthropomorphism and surface features

- Epley, Waytz, Cacioppo (2007). "On seeing human: A three-factor theory of anthropomorphism." *Psychological Review*.
- Salles, Evers, Farisco (2020). "Anthropomorphism in AI." *AJOB Neuroscience*.

---

## Timeline for the build

| Hour | Task |
|------|------|
| 1 | Scaffolding, agent classes, PD game engine |
| 2 | Scripted agents, behavior matcher, observer with rubric |
| 3 | Streamlit UI with live game panels |
| 4 | Run experiments, collect data |
| 5 | Analysis, stats, plots |
| 6 | Slides, script, anticipated questions |

Tight but doable.

---

## Why this project matters

The immediate goal is a LEMAS presentation. The deeper bet is that mirage-style empirical work is an underexplored gap in the AISS-relevant literature. There is a lot of philosophical argument about what LLMs do and don't have. There is much less empirical work showing *how* observers over-attribute minds and through *what specific mechanisms*. A clean behavioral control plus a structured rubric plus a regression on surface features is a serviceable research skeleton that extends naturally to human observers, different games, different models, and different rubrics.

If the results sting, good. That is the experiment doing its job.
