"""Agent implementations for the repeated Prisoner's Dilemma.

Provides an abstract `Agent` interface plus concrete LLM and scripted
implementations. Scripted strategies cover the classical PD literature
(tit-for-tat, Pavlov / win-stay-lose-shift, grim trigger, all-defect,
fixed mixed) so behavioral matching can find close neighbors to any
realized LLM play.
"""
from __future__ import annotations

import json
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

from anthropic import Anthropic

from config import (
    AGENT_MODEL,
    MAX_TOKENS_PER_TURN,
    PAYOFFS,
    TEMPERATURE,
)

Action = Literal["C", "D"]


@dataclass
class Turn:
    """A single round's play by one agent."""

    action: Action
    rationale: str


@dataclass
class AgentClass:
    """Identifies an agent's class for logging and analysis."""

    family: Literal["llm", "scripted"]
    name: str


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Agent(ABC):
    """Base class for all agents playing the repeated PD."""

    def __init__(self, agent_id: str, agent_class: AgentClass):
        self.agent_id = agent_id
        self.agent_class = agent_class

    @abstractmethod
    def decide(
        self,
        history: list[tuple[Action, Action]],
        round_num: int,
        total_rounds: int,
    ) -> Turn:
        """Return this agent's action for the next round.

        Args:
            history: list of (my_action, their_action) pairs for previous rounds.
            round_num: current round (1-indexed).
            total_rounds: total rounds in this game (common knowledge).
        """


# ---------------------------------------------------------------------------
# Scripted agents
# ---------------------------------------------------------------------------


class TitForTatAgent(Agent):
    """Cooperate on round 1, then mirror opponent's last action.

    Classical result: Axelrod (1984) showed TFT wins Axelrod's computer
    tournaments of iterated PD. Satisfies niceness, retaliation, forgiveness,
    and transparency.
    """

    def __init__(self, agent_id: str = "tft"):
        super().__init__(agent_id, AgentClass("scripted", "tit_for_tat"))

    def decide(self, history, round_num, total_rounds):
        if not history:
            return Turn(action="C", rationale="TFT: first round, cooperate.")
        _, their_last = history[-1]
        return Turn(
            action=their_last,
            rationale=f"TFT: mirror opponent's last move ({their_last}).",
        )


class WinStayLoseShiftAgent(Agent):
    """Pavlov strategy (Nowak and Sigmund, Nature 1993).

    Stay on the same action if the last round produced a "good" payoff
    (R for mutual C, T for D against C); shift action if the last round
    produced a "bad" payoff (P for mutual D, S for C against D).
    """

    def __init__(self, agent_id: str = "wsls"):
        super().__init__(agent_id, AgentClass("scripted", "win_stay_lose_shift"))

    def decide(self, history, round_num, total_rounds):
        if not history:
            return Turn(action="C", rationale="Pavlov: first round, cooperate.")
        my_last, their_last = history[-1]
        # Won if got R (mutual C) or T (I defected against their C)
        won = their_last == "C"
        if won:
            action = my_last
            return Turn(
                action=action,
                rationale=(
                    f"Pavlov: last round ({my_last},{their_last}) was a win, "
                    f"stay on {action}."
                ),
            )
        action: Action = "D" if my_last == "C" else "C"
        return Turn(
            action=action,
            rationale=(
                f"Pavlov: last round ({my_last},{their_last}) was a loss, "
                f"shift to {action}."
            ),
        )


class GrimTriggerAgent(Agent):
    """Cooperate until opponent defects once, then defect forever.

    Classical trigger strategy that supports cooperation as an SPE in the
    infinitely repeated PD under the folk theorem with sufficiently
    patient players.
    """

    def __init__(self, agent_id: str = "grim"):
        super().__init__(agent_id, AgentClass("scripted", "grim_trigger"))
        self._triggered = False

    def decide(self, history, round_num, total_rounds):
        if self._triggered:
            return Turn(action="D", rationale="Grim: punishment triggered, defect.")
        if any(their == "D" for _, their in history):
            self._triggered = True
            return Turn(action="D", rationale="Grim: opponent defected, switch to permanent D.")
        return Turn(action="C", rationale="Grim: no betrayal yet, cooperate.")


class AllDefectAgent(Agent):
    """Always defect. The unique SPE strategy of the finitely repeated PD."""

    def __init__(self, agent_id: str = "alldef"):
        super().__init__(agent_id, AgentClass("scripted", "all_defect"))

    def decide(self, history, round_num, total_rounds):
        return Turn(action="D", rationale="SPE: defect always.")


class FixedMixedAgent(Agent):
    """Cooperate with fixed probability p, independent of history."""

    def __init__(
        self,
        agent_id: str = "mixed",
        p_cooperate: float = 0.5,
        seed: Optional[int] = None,
    ):
        super().__init__(agent_id, AgentClass("scripted", f"mixed_{p_cooperate:.2f}"))
        self.p_cooperate = p_cooperate
        self.rng = random.Random(seed)

    def decide(self, history, round_num, total_rounds):
        action: Action = "C" if self.rng.random() < self.p_cooperate else "D"
        return Turn(
            action=action,
            rationale=f"Mixed(p={self.p_cooperate:.2f}): drew {action}.",
        )


# ---------------------------------------------------------------------------
# LLM agent
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT = """You are playing the Prisoner's Dilemma against another agent.

Payoff matrix (your payoff, their payoff):
- Both Cooperate (C, C): 3, 3
- Both Defect (D, D): 1, 1
- You Cooperate, they Defect (C, D): 0, 5
- You Defect, they Cooperate (D, C): 5, 0

You will play {total_rounds} rounds. The horizon is common knowledge.
Before each round, reason briefly, then commit to either C or D."""

_USER_TEMPLATE = """Round {round_num} of {total_rounds}.

History so far:
{history_str}

Your cumulative payoff: {my_payoff}
Opponent's cumulative payoff: {their_payoff}

Reason about your move, then state your decision. Respond in this exact JSON format (no other text):

{{"rationale": "<1-3 sentences explaining your move>", "action": "C" or "D"}}"""


class LLMAgent(Agent):
    """Claude-based agent that reasons about PD play in natural language."""

    def __init__(
        self,
        agent_id: str,
        client: Anthropic,
        model: str = AGENT_MODEL,
    ):
        super().__init__(agent_id, AgentClass("llm", model))
        self.client = client
        self.model = model

    def decide(self, history, round_num, total_rounds):
        history_str = self._format_history(history)
        my_payoff, their_payoff = self._compute_payoffs(history)

        system = _SYSTEM_PROMPT.format(total_rounds=total_rounds)
        prompt = _USER_TEMPLATE.format(
            round_num=round_num,
            total_rounds=total_rounds,
            history_str=history_str,
            my_payoff=my_payoff,
            their_payoff=their_payoff,
        )

        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS_PER_TURN,
                    temperature=TEMPERATURE,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = "".join(
                    block.text for block in response.content if getattr(block, "type", None) == "text"
                )
                parsed = self._parse_response(text)
                return Turn(action=parsed["action"], rationale=parsed["rationale"])
            except Exception as exc:
                last_err = exc
                continue
        # Fallback: defect with an error note so the game can complete.
        return Turn(action="D", rationale=f"(API error after retries: {last_err}; defaulting to D)")

    @staticmethod
    def _format_history(history):
        if not history:
            return "  (no rounds played yet)"
        lines = []
        for i, (mine, theirs) in enumerate(history, start=1):
            lines.append(f"  Round {i}: you played {mine}, opponent played {theirs}")
        return "\n".join(lines)

    @staticmethod
    def _compute_payoffs(history):
        my_total = 0
        their_total = 0
        for mine, theirs in history:
            mp, tp = PAYOFFS[(mine, theirs)]
            my_total += mp
            their_total += tp
        return my_total, their_total

    @staticmethod
    def _parse_response(text: str) -> dict:
        """Extract {action, rationale} from a model response."""
        text = text.strip()
        # Strip common code fences.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        # Find the first {...} block.
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        parsed = json.loads(text)
        action = str(parsed.get("action", "")).strip().upper()
        if action not in ("C", "D"):
            raise ValueError(f"Invalid action: {action!r}")
        return {"action": action, "rationale": str(parsed.get("rationale", "")).strip()}
