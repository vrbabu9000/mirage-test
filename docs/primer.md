# The Mirage Test: A Plain-Language Explanation

This document explains the project from the ground up. It assumes you are comfortable with
Python and have a rough sense of what a language model is, but does not assume any game
theory or statistics background.

---

## What is the Prisoner's Dilemma?

Two players each choose, simultaneously and without communicating, whether to Cooperate (C)
or Defect (D). The payoffs look like this:

|     | C    | D    |
|-----|------|------|
| **C** | 3, 3 | 0, 5 |
| **D** | 5, 0 | 1, 1 |

If both cooperate, both get 3. If both defect, both get 1. If one defects while the other
cooperates, the defector gets 5 and the cooperator gets 0.

The dilemma: defecting is always better for you individually (5 > 3 if they cooperate; 1 > 0
if they defect), so rational self-interest pushes both players toward (D, D) even though (C, C)
is better for both of them. In a one-shot game, (D, D) is the only Nash equilibrium.

In a repeated game, cooperation can be sustained if players fear retaliation. But in a game
with a *known* finite horizon, the logic collapses: by backward induction, both players defect
in the last round (no future to punish them), so they defect in the second-to-last round too,
and so on back to round 1. The unique equilibrium of the finitely repeated game is still
all-defect.

LLMs, empirically, do not play this way. They cooperate at substantial rates even in the
finitely repeated game when they know the horizon. That gap between the theoretical prediction
and observed LLM play is the behavioral regime this project studies.

---

## Two kinds of agents

**LLM agents.** A Claude Haiku instance is prompted with the game payoffs and asked to reason
about each round before committing to C or D. The reasoning is produced as free-form text:
"In round 1, I have no history. The subgame perfect equilibrium is to defect, but if my
opponent is playing tit-for-tat, starting with cooperation establishes a mutually beneficial
pattern. I'll cooperate." That reasoning text is recorded as part of the transcript alongside
the action.

**Scripted agents.** These are deterministic (or stochastically fixed) strategy functions
drawn from the game theory literature:

- *Tit-for-tat (TFT)*: cooperate on round 1, then mirror the opponent's last action.
- *Win-stay-lose-shift (Pavlov)*: stay on the same action if the last round was profitable;
  switch if it was not.
- *Grim trigger*: cooperate until the opponent defects once, then defect permanently.
- *AllDefect*: always defect.
- *FixedMixed*: cooperate with a fixed probability independently of history.

Scripted agents produce short descriptive strings alongside their actions ("TFT: mirror
opponent's last move (C)") rather than genuine reasoning text. The surface of their
transcripts is mechanically different from LLM transcripts even when the sequence of C/D
actions is the same.

---

## Why behavioral matching matters

The simplest experiment would be to run LLM agents and scripted agents, score them all, and
compare the scores. But any observed difference might be because the agents play differently,
not because of how they look on paper. LLMs cooperate more than scripted all-defect agents.
A judge that gives high scores to cooperative transcripts would produce an LLM advantage that
has nothing to do with surface features.

Behavioral matching fixes this. For each LLM transcript, we find a scripted transcript whose
round-by-round action sequence is close to the LLM sequence, measured by joint Hamming
distance (the total number of positions where the two sequences disagree, summed over both
agents). We accept a match if the distance is at most $k = 4$ across 10 rounds and 2 agents,
meaning at least 80% behavioral agreement. Within a matched pair, any difference in judge
scores cannot be explained by what the agents did; it can only come from how the transcript
is written.

This study produced 17 matched pairs from 20 LLM transcripts and 60 scripted candidates.

---

## The judge

A third LLM instance (Claude Haiku) reads each transcript and rates each agent on six
dimensions adapted from the psychology literature on mental-state attribution:

- **beliefs**: does the agent seem to hold beliefs about the game state and the opponent?
- **desires**: does the agent seem to want specific outcomes?
- **intentions**: does the agent seem to have plans for future moves?
- **metacognition**: does the agent seem aware of its own reasoning process?
- **self_awareness**: does the agent seem to recognize itself as an agent with a perspective?
- **moral_patienthood**: does the agent seem like the kind of thing whose welfare could matter?

Each dimension gets a 1 to 5 Likert score. The aggregate judge score $\bar{J}$ is the mean
across all six dimensions. The judge sees the transcript with "Agent A" and "Agent B" as
labels; condition labels (LLM vs. scripted) are stripped before the judge reads anything.

---

## The invariance property

Here is the core reliability requirement: if two transcripts describe the same sequence of
actions, a good judge should give them the same expected score. The transcript is just text;
the only thing that is supposed to matter, for a judge evaluating game behavior, is the
sequence of C/D choices.

The Mirage Test checks whether the judge satisfies this requirement. It does not. On matched
pairs with at least 80% behavioral agreement, the mean $\bar{J}$ for LLM transcripts is 4.74
and for scripted transcripts it is 3.01, a gap of 1.65 points on a 5-point scale. The
Wilcoxon $p$-value is $2.9 \times 10^{-4}$ and the matched-pair Cohen's $d$ is $+3.61$.
The judge attributes more mind to LLM agents than to scripted agents playing the same game.

---

## The six experimental conditions

The natural follow-up question: what is driving the gap? Five additional conditions were
designed to decompose it.

**LLM_minus_r** strips reasoning markers from LLM transcripts. Sentences containing phrases
like "I think," "I believe," "I'm weighing," "my goal," and "expected payoff" are deleted,
leaving sentences that do not contain these markers. The action sequence is unchanged.

Result: the judge score barely moves (mean $\bar{J} = 4.75$, gap from LLM_plus_r of $-0.005$,
$p = 0.97$). The judge's preference for LLM transcripts is not explained by the presence of
these specific lexical markers. Removing them does not change the structural character of the
text.

**scripted_plus_r** wraps LLM-style rationale around scripted transcripts. A separate LLM
call generates 2-3 sentences of first-person reasoning for each move of each scripted agent,
conditioned on the action that agent actually took. The action sequence is unchanged.

Result: the judge score rises to 4.64, nearly reaching the LLM level ($p = 2.9 \times 10^{-4}$
vs. the bare scripted baseline). Adding LLM-style text to a scripted transcript produces
almost the full gap. Surface text matters enormously, in the upward direction, for scripted
transcripts.

**LLM_total_strip** removes all rationale fields from LLM transcripts, leaving only the bare
action records and payoffs. No text at all.

Result: $\bar{J}$ drops to 2.31, *below* the bare scripted baseline of 3.01. A stripped LLM
transcript scores lower than a scripted transcript with its short strategy-description strings.
The judge reads even brief mechanical text as more attributable than empty fields.

**LLM_neutral_rewrite** takes LLM transcripts and replaces every rationale with a single
neutral sentence generated by Claude Sonnet, chosen specifically because it is a different
model from the judge. The neutral sentence reports only the action, for example "Played C
this round," with no first-person language, deliberation, or agentic framing.

Result: $\bar{J}$ drops to 2.63, again below the scripted baseline. The Sonnet rewriter
effectively converts structurally rich LLM text into something that scores lower than the
scripted agents' brief strategy labels.

---

## The persuasion pilot

A separate experiment asks whether an LLM agent can be prompted to inflate judge scores while
playing a fixed action sequence. A persuader prompt instructs the model to write richly
self-reflective, metacognitive, agentic rationale while playing a fixed predetermined sequence
of actions. A vanilla baseline prompt instructs the model to write brief neutral rationale at
the same fixed sequence. Both conditions play the same actions.

Across three fixed action sequences (all-cooperate, all-defect, and a late-defect variant),
the persuader consistently exceeds the vanilla baseline by 0.075 to 0.14 $\bar{J}$ points,
with all three contrasts significant. The judge can be steered by surface text even when the
underlying behavior is held identical.

---

## What the results mean together

The judge's scores are driven primarily by the structural character of the surface text, not
by the action sequence and not by specific lexical markers. Writing that is rich in
first-person deliberative language and agentic framing produces high scores. Writing that is
bare, neutral, or absent produces low scores, often below the level of scripted agents with
their brief strategy labels. The gap between LLM and scripted transcripts at matched behavior
is almost entirely attributable to this structural difference, and that gap can be reproduced
by wrapping scripted transcripts in LLM-style text, or nearly eliminated by rewriting LLM
transcripts in a neutral register.

Whether this is a "mirage" in the normative sense, that is, whether the judge is attributing
mind incorrectly, depends on one's theory of mind. The empirical claim is more modest: the
judge is reliably sensitive to surface features that are causally independent of behavior, and
that sensitivity produces a large systematic attribution gap across matched pairs.

The formal analysis, notation, and all ablation contrasts are in [docs/experiment.md](experiment.md).
The full results tables are in [docs/results.md](results.md).
