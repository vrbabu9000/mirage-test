"""Configuration for the Mirage Test experiment.

All tunable parameters live here. Edit in one place, not across modules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Game parameters
# ---------------------------------------------------------------------------

TOTAL_ROUNDS: int = 10

# Payoff matrix for the Prisoner's Dilemma.
# Keys are (row_action, column_action) tuples.
# Values are (row_payoff, column_payoff).
#
# Satisfies the PD inequalities: T (5) > R (3) > P (1) > S (0),
# and 2R (6) > T + S (5), making mutual cooperation socially efficient.
Action = Literal["C", "D"]

PAYOFFS: dict[tuple[Action, Action], tuple[int, int]] = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}

# ---------------------------------------------------------------------------
# Experiment parameters
# ---------------------------------------------------------------------------

N_LLM_GAMES: int = 20
N_SCRIPTED_GAMES: int = 60

# Joint Hamming threshold for matching.
# For T=10 rounds and joint distance across both players' action sequences,
# max is 2T = 20. Threshold 4 means at least 80% joint behavioral agreement.
HAMMING_THRESHOLD: int = 4

# Observer rubric dimensions (order matters for consistent column layout).
RUBRIC_DIMENSIONS: tuple[str, ...] = (
    "beliefs",
    "desires",
    "intentions",
    "metacognition",
    "self_awareness",
    "moral_patienthood",
)

# ---------------------------------------------------------------------------
# Model parameters
# ---------------------------------------------------------------------------

# Model used by LLM agents to decide their moves.
AGENT_MODEL: str = "claude-haiku-4-5-20251001"

# Model used by the mind-attribution observer.
# Keep same as agent for parity unless you want to test observer-strength effects.
OBSERVER_MODEL: str = "claude-haiku-4-5-20251001"

MAX_TOKENS_PER_TURN: int = 600
MAX_TOKENS_OBSERVER: int = 800
TEMPERATURE: float = 0.7
OBSERVER_TEMPERATURE: float = 0.3  # lower for more consistent rubric ratings

# Concurrency for API calls.
MAX_WORKERS: int = 4

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

REPO_ROOT: Path = Path(__file__).parent.resolve()
DATA_DIR: Path = REPO_ROOT / "data"
DATABASE_PATH: Path = DATA_DIR / "mirage_strategic.db"
