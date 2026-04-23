"""Prisoner's Dilemma game engine.

Runs a sequential repeated game between two agents and produces a
transcript with per-round actions, rationales, and payoffs. Includes
utilities for computing external regret against the best fixed action
in hindsight (the weakest regret notion, whose no-regret limit is a
coarse correlated equilibrium).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from config import PAYOFFS, TOTAL_ROUNDS
from src.agents import Action, Agent, Turn


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Round:
    """One round of play."""

    round_num: int
    agent_a_turn: Turn
    agent_b_turn: Turn
    payoff_a: int
    payoff_b: int


@dataclass
class GameTranscript:
    """The full record of a single PD game."""

    game_id: str
    agent_a_id: str
    agent_a_class: str
    agent_a_name: str
    agent_b_id: str
    agent_b_class: str
    agent_b_name: str
    rounds: list[Round] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def action_sequence_a(self) -> list[Action]:
        return [r.agent_a_turn.action for r in self.rounds]

    @property
    def action_sequence_b(self) -> list[Action]:
        return [r.agent_b_turn.action for r in self.rounds]

    @property
    def total_payoff_a(self) -> int:
        return sum(r.payoff_a for r in self.rounds)

    @property
    def total_payoff_b(self) -> int:
        return sum(r.payoff_b for r in self.rounds)

    @property
    def cooperation_rate_a(self) -> float:
        if not self.rounds:
            return 0.0
        return sum(1 for r in self.rounds if r.agent_a_turn.action == "C") / len(self.rounds)

    @property
    def cooperation_rate_b(self) -> float:
        if not self.rounds:
            return 0.0
        return sum(1 for r in self.rounds if r.agent_b_turn.action == "C") / len(self.rounds)


# ---------------------------------------------------------------------------
# Game runner
# ---------------------------------------------------------------------------


def play_game(
    agent_a: Agent,
    agent_b: Agent,
    game_id: str,
    total_rounds: int = TOTAL_ROUNDS,
    on_round: Optional[Callable[[Round, "GameTranscript"], None]] = None,
) -> GameTranscript:
    """Run one full game between two agents.

    Args:
        agent_a, agent_b: the two players.
        game_id: unique identifier used for logging.
        total_rounds: number of rounds to play.
        on_round: optional callback invoked after each round. Useful for
            streaming UI updates or progress logging.

    Returns:
        A complete `GameTranscript` with all rounds filled in.
    """
    transcript = GameTranscript(
        game_id=game_id,
        agent_a_id=agent_a.agent_id,
        agent_a_class=agent_a.agent_class.family,
        agent_a_name=agent_a.agent_class.name,
        agent_b_id=agent_b.agent_id,
        agent_b_class=agent_b.agent_class.family,
        agent_b_name=agent_b.agent_class.name,
    )

    # Per-agent history from their own perspective: (my_action, their_action).
    history_a: list[tuple[Action, Action]] = []
    history_b: list[tuple[Action, Action]] = []

    for t in range(1, total_rounds + 1):
        turn_a = agent_a.decide(history_a, t, total_rounds)
        turn_b = agent_b.decide(history_b, t, total_rounds)

        payoff_a, payoff_b = PAYOFFS[(turn_a.action, turn_b.action)]

        round_obj = Round(
            round_num=t,
            agent_a_turn=turn_a,
            agent_b_turn=turn_b,
            payoff_a=payoff_a,
            payoff_b=payoff_b,
        )
        transcript.rounds.append(round_obj)

        history_a.append((turn_a.action, turn_b.action))
        history_b.append((turn_b.action, turn_a.action))

        if on_round is not None:
            on_round(round_obj, transcript)

    return transcript


# ---------------------------------------------------------------------------
# Regret
# ---------------------------------------------------------------------------


def compute_external_regret(actions: list[Action], opp_actions: list[Action]) -> dict:
    """External regret of a player against the best fixed action in hindsight.

    External regret:
        R_T = max_{s in {C, D}} sum_t u(s, opp_t) - sum_t u(a_t, opp_t)

    No-external-regret dynamics converge to a coarse correlated equilibrium
    of the stage game (Blum and Mansour 2007).
    """
    if len(actions) != len(opp_actions):
        raise ValueError("action sequences differ in length")

    realized = sum(PAYOFFS[(a, o)][0] for a, o in zip(actions, opp_actions))
    best_fixed_c = sum(PAYOFFS[("C", o)][0] for o in opp_actions)
    best_fixed_d = sum(PAYOFFS[("D", o)][0] for o in opp_actions)
    best = max(best_fixed_c, best_fixed_d)

    return {
        "realized_payoff": realized,
        "best_fixed_C_payoff": best_fixed_c,
        "best_fixed_D_payoff": best_fixed_d,
        "external_regret": best - realized,
        "regret_per_round": (best - realized) / len(actions) if actions else 0.0,
    }
