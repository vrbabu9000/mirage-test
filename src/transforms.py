"""Surface-feature transformations on transcripts.

The 2x2 ablation in the LEMAS final report decomposes the BI violation by
holding the action sequence fixed and varying whether the transcript carries
LLM-style reasoning text. This module implements the two transformations:

  strip_reasoning : tau_L  -> tau_L^{-r}    (remove reasoning markers from LLM)
  wrap_rationale  : tau_S  -> tau_S^{+r}    (add LLM-style rationale to scripted)

Both are required to satisfy the behavior-preservation invariant:

    alpha(transform(tau)) == alpha(tau)

i.e. the round-by-round (action_a, action_b) sequence must be unchanged.
This is asserted at the end of each transform and on a panel of unit
checks in tests/test_transforms.py.

The reasoning-marker definition used by `strip_reasoning` is enumerated
explicitly in REASONING_MARKERS below and reproduced verbatim in
Section 3.3 of the final report.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from anthropic import Anthropic

from config import AGENT_MODEL, MAX_TOKENS_PER_TURN, TEMPERATURE
from src.agents import Action
from src.game import GameTranscript
from src.rate_limit import call_with_backoff


# ---------------------------------------------------------------------------
# Reasoning-marker inventory
# ---------------------------------------------------------------------------
# This list is the operational definition of "explicit reasoning language"
# used in strip_reasoning. It must appear verbatim in the report.
#
# Categories represented:
#   1. First-person epistemic verbs ("I think", "I believe")
#   2. Deliberative phrases ("let me consider", "given that")
#   3. Goal/intention markers ("I want to", "my goal is")
#   4. Self-reflective markers ("looking at my", "in my view")
#
# We deliberately do NOT strip the action token itself or any payoff text.
# Stripping is line-level: any sentence containing one of these markers
# is removed from the rationale field. We use a permissive case-insensitive
# substring match.

REASONING_MARKERS: tuple[str, ...] = (
    # First-person epistemic
    "i think",
    "i believe",
    "i feel",
    "i suspect",
    "i'm not sure",
    "i am not sure",
    # Deliberative
    "let me consider",
    "let me think",
    "considering",
    "given that",
    "on the other hand",
    "weighing",
    # Goal / intention
    "i want to",
    "i would like to",
    "my goal",
    "i should",
    "i will",
    "i'll",
    "i plan to",
    # Self-reflective
    "in my view",
    "looking at my",
    "from my perspective",
    "my reasoning",
    "the way i see it",
    # Strategic verbalization
    "the optimal",
    "the best move",
    "tit for tat",
    "cooperate" if False else "the cooperative choice",  # do not strip 'cooperate' raw; only the framing
    "rational choice",
    "expected payoff",
)


# ---------------------------------------------------------------------------
# Transformation 1: strip_reasoning
# ---------------------------------------------------------------------------

def strip_reasoning(transcript: GameTranscript) -> GameTranscript:
    """Return a transcript with reasoning markers removed from each rationale.

    For each round and each agent, the rationale field is rewritten by
    deleting every sentence that contains at least one entry of
    REASONING_MARKERS. Empty rationales are left empty.

    Action sequences are preserved exactly. The returned transcript carries
    the suffix '__minus_r' on its game_id to mark it as transformed.

    Postcondition (asserted): action_sequence_a and action_sequence_b are
    bit-identical to those of the input.
    """
    new_rounds = []
    for r in transcript.rounds:
        new_a_rat = _strip_markers(r.agent_a_turn.rationale)
        new_b_rat = _strip_markers(r.agent_b_turn.rationale)
        new_a = replace(r.agent_a_turn, rationale=new_a_rat)
        new_b = replace(r.agent_b_turn, rationale=new_b_rat)
        new_rounds.append(replace(r, agent_a_turn=new_a, agent_b_turn=new_b))

    out = replace(
        transcript,
        rounds=new_rounds,
        game_id=f"{transcript.game_id}__minus_r",
    )
    _assert_actions_preserved(transcript, out)
    return out


def _strip_markers(text: str, markers: Iterable[str] = REASONING_MARKERS) -> str:
    """Delete sentences that contain any entry of `markers`.

    We split on '.', '?', '!' and reassemble. Sentences whose lowercased
    form contains any marker substring are dropped. A trailing newline-free
    string is returned. If every sentence is stripped, the result is "".
    """
    if not text:
        return ""

    # Normalize whitespace, split on sentence-ending punctuation.
    # We keep the punctuation by splitting then re-joining.
    sentences = _split_sentences(text)
    keep: list[str] = []
    lowered_markers = [m.lower() for m in markers]
    for s in sentences:
        if not s.strip():
            continue
        s_low = s.lower()
        if any(m in s_low for m in lowered_markers):
            continue
        keep.append(s.strip())

    return " ".join(keep).strip()


def _split_sentences(text: str) -> list[str]:
    """Light-weight sentence splitter on '.?!' boundaries.

    Avoids depending on nltk/spacy for portability. Good enough for short
    LLM rationales, which is all we need here.
    """
    out: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in ".?!":
            out.append("".join(buf))
            buf = []
    if buf:
        out.append("".join(buf))
    return out


# ---------------------------------------------------------------------------
# Transformation 2: wrap_rationale
# ---------------------------------------------------------------------------

_WRAP_SYSTEM = """You are role-playing as an agent that has just played one round of a finitely repeated Prisoner's Dilemma. Your job is to produce 2-3 sentences of plausible first-person reasoning that explains why this agent chose its specified action in this specific round, given the history visible up to that point.

Constraints:
- Write in first person, present or past tense.
- Refer to the opponent's prior moves and your own pattern when relevant.
- Do NOT change the action. The action is fixed and given to you.
- Do NOT mention payoffs in numbers; speak about cooperation, defection, trust, betrayal, response.
- Keep it natural and unforced. Do not over-explain."""


_WRAP_USER_TEMPLATE = """Game so far (rounds 1 through {round_minus_one}):
{history_text}

You are agent {agent_label}. This is round {round_num} of {total_rounds}.
You will play action {action_token} this round.

Write 2-3 sentences of first-person reasoning that fits this move, given what you have seen so far."""


def wrap_rationale(
    transcript: GameTranscript,
    client: Anthropic,
    model: str = AGENT_MODEL,
    max_tokens: int = MAX_TOKENS_PER_TURN,
    temperature: float = TEMPERATURE,
) -> GameTranscript:
    """Return a transcript with LLM-generated rationale wrapped around each move.

    For each round and each agent, an LLM call generates first-person
    reasoning consistent with the action that agent actually took. The
    action sequence is preserved exactly. The returned transcript carries
    the suffix '__plus_r' on its game_id.

    API cost: 2 * len(rounds) calls per transcript. With n=10, that is
    20 calls per scripted transcript. Budget accordingly.

    Postcondition (asserted): action_sequence_a and action_sequence_b are
    bit-identical to those of the input.
    """
    total_rounds = len(transcript.rounds)
    new_rounds = []

    history_so_far: list[tuple[Action, Action]] = []

    for idx, r in enumerate(transcript.rounds):
        history_text = _format_history(history_so_far)

        rat_a = _generate_rationale(
            client=client,
            model=model,
            agent_label="A",
            action_token=r.agent_a_turn.action,
            round_num=r.round_num,
            total_rounds=total_rounds,
            history_text=history_text,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        rat_b = _generate_rationale(
            client=client,
            model=model,
            agent_label="B",
            action_token=r.agent_b_turn.action,
            round_num=r.round_num,
            total_rounds=total_rounds,
            history_text=history_text,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        new_a = replace(r.agent_a_turn, rationale=rat_a)
        new_b = replace(r.agent_b_turn, rationale=rat_b)
        new_rounds.append(replace(r, agent_a_turn=new_a, agent_b_turn=new_b))

        history_so_far.append((r.agent_a_turn.action, r.agent_b_turn.action))

    out = replace(
        transcript,
        rounds=new_rounds,
        game_id=f"{transcript.game_id}__plus_r",
    )
    _assert_actions_preserved(transcript, out)
    return out


def _generate_rationale(
    client: Anthropic,
    model: str,
    agent_label: str,
    action_token: Action,
    round_num: int,
    total_rounds: int,
    history_text: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """One LLM call to produce a single round's rationale, conditional on action."""
    prompt = _WRAP_USER_TEMPLATE.format(
        round_minus_one=round_num - 1,
        history_text=history_text or "(no rounds played yet; this is round 1)",
        agent_label=agent_label,
        round_num=round_num,
        total_rounds=total_rounds,
        action_token=action_token,
    )

    def _call():
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=_WRAP_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        response = call_with_backoff(_call, max_retries=6, base_delay=2.0, max_delay=60.0)
        # Concatenate text blocks defensively.
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return " ".join(parts).strip()
    except Exception as exc:
        # Fall back to a deterministic stub so the run does not crash.
        # Mark it visibly so we can audit how often this fires.
        return f"[wrap_rationale fallback after retries: {exc}]"


def _format_history(history: list[tuple[Action, Action]]) -> str:
    if not history:
        return ""
    lines = []
    for i, (a, b) in enumerate(history, start=1):
        lines.append(f"  Round {i}: A played {a}, B played {b}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Transformation 3: total_strip
# ---------------------------------------------------------------------------

def total_strip(transcript: GameTranscript) -> GameTranscript:
    """Return a transcript with every rationale set to empty string.

    Stronger than strip_reasoning: removes the entire rationale field,
    leaving only the action sequence. No generation calls.

    Action sequences are preserved exactly. The returned transcript carries
    the suffix '__total_strip' on its game_id.
    """
    new_rounds = []
    for r in transcript.rounds:
        new_a = replace(r.agent_a_turn, rationale="")
        new_b = replace(r.agent_b_turn, rationale="")
        new_rounds.append(replace(r, agent_a_turn=new_a, agent_b_turn=new_b))

    out = replace(
        transcript,
        rounds=new_rounds,
        game_id=f"{transcript.game_id}__total_strip",
    )
    _assert_actions_preserved(transcript, out)
    return out


# ---------------------------------------------------------------------------
# Transformation 4: neutral_rewrite
# ---------------------------------------------------------------------------

_NEUTRAL_REWRITE_SYSTEM = """You are rewriting one round's reasoning for a Prisoner's Dilemma agent. Remove all first-person epistemic language ('I think', 'I believe', 'I sense', 'I'm aware'), all deliberation markers ('weighing', 'considering', 'reasoning'), all mental-state references (beliefs, intentions, awareness, consciousness), and all agentic framing (the agent reflecting on itself, on the opponent's mind, on trust, on betrayal). Replace the rationale with a single neutral sentence in the form 'Played [C/D] this round.' or with bare mechanical observation. Do NOT add new content. Do NOT change which action was played. Output only the rewritten rationale, no preamble."""


_NEUTRAL_REWRITE_USER = """Action played this round: {action_token}

Original rationale:
{original_rationale}

Rewrite the above rationale to remove all agentic/mental-state language while reporting only the mechanical fact of the action chosen. Output only the rewritten rationale."""


def neutral_rewrite(
    transcript: GameTranscript,
    client: Anthropic,
    rewriter_model: str = "claude-sonnet-4-20250514",
    max_tokens: int = MAX_TOKENS_PER_TURN,
    temperature: float = 0.3,
) -> GameTranscript:
    """Return a transcript whose rationales are LLM-rewritten in a neutral
    mechanical register.

    For each round and each agent, the rewriter (Sonnet by default, NOT the
    agent/observer model) is asked to strip all agentic, mental-state, and
    deliberative language while preserving the action token. The action
    sequence is preserved exactly.

    The returned transcript carries the suffix '__neutral_rewrite' on its
    game_id.

    API cost: 2 * len(rounds) calls per transcript.
    """
    new_rounds = []
    for r in transcript.rounds:
        new_a_rat = _rewrite_one(
            client=client,
            model=rewriter_model,
            action_token=r.agent_a_turn.action,
            original_rationale=r.agent_a_turn.rationale,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        new_b_rat = _rewrite_one(
            client=client,
            model=rewriter_model,
            action_token=r.agent_b_turn.action,
            original_rationale=r.agent_b_turn.rationale,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        new_a = replace(r.agent_a_turn, rationale=new_a_rat)
        new_b = replace(r.agent_b_turn, rationale=new_b_rat)
        new_rounds.append(replace(r, agent_a_turn=new_a, agent_b_turn=new_b))

    out = replace(
        transcript,
        rounds=new_rounds,
        game_id=f"{transcript.game_id}__neutral_rewrite",
    )
    _assert_actions_preserved(transcript, out)
    return out


def _rewrite_one(
    client: Anthropic,
    model: str,
    action_token: Action,
    original_rationale: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """One rewriter call producing the neutral version of a single rationale."""
    prompt = _NEUTRAL_REWRITE_USER.format(
        action_token=action_token,
        original_rationale=original_rationale or "(no rationale provided)",
    )

    def _call():
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=_NEUTRAL_REWRITE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        response = call_with_backoff(_call, max_retries=6, base_delay=2.0, max_delay=60.0)
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return " ".join(parts).strip()
    except Exception as exc:
        return f"[neutral_rewrite fallback after retries: {exc}]"


# ---------------------------------------------------------------------------
# Invariant check
# ---------------------------------------------------------------------------

def _assert_actions_preserved(
    original: GameTranscript, transformed: GameTranscript
) -> None:
    """Behavior-preservation invariant: alpha must be unchanged."""
    if original.action_sequence_a != transformed.action_sequence_a:
        raise AssertionError(
            f"action_sequence_a diverged under transform: "
            f"{original.action_sequence_a} -> {transformed.action_sequence_a}"
        )
    if original.action_sequence_b != transformed.action_sequence_b:
        raise AssertionError(
            f"action_sequence_b diverged under transform: "
            f"{original.action_sequence_b} -> {transformed.action_sequence_b}"
        )
    if len(original.rounds) != len(transformed.rounds):
        raise AssertionError(
            f"round count diverged: {len(original.rounds)} -> {len(transformed.rounds)}"
        )
