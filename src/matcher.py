"""Behavioral matching between LLM and scripted transcripts.

We use joint Hamming distance across both players' action sequences as
the matching metric. Greedy one-to-one matching minimizes per-pair
distance; pairs above the threshold are dropped.

For T = 10 rounds, joint distance ranges from 0 (identical action
sequences for both players) to 20 (completely disjoint). A threshold
of 4 means at least 16/20 = 80% behavioral agreement.
"""
from __future__ import annotations

from dataclasses import dataclass

from config import HAMMING_THRESHOLD
from src.agents import Action
from src.game import GameTranscript


def hamming_distance(a: list[Action], b: list[Action]) -> int:
    """Number of positions at which two action sequences differ."""
    if len(a) != len(b):
        raise ValueError(
            f"action sequences have different lengths: {len(a)} vs {len(b)}"
        )
    return sum(1 for x, y in zip(a, b) if x != y)


def joint_hamming(t1: GameTranscript, t2: GameTranscript) -> int:
    """Joint Hamming distance across both players' action sequences.

    Defined as d_H(action_a1, action_a2) + d_H(action_b1, action_b2).
    """
    da = hamming_distance(t1.action_sequence_a, t2.action_sequence_a)
    db = hamming_distance(t1.action_sequence_b, t2.action_sequence_b)
    return da + db


@dataclass
class MatchedPair:
    """A pair of (LLM transcript, scripted transcript) matched by behavior."""

    llm_transcript: GameTranscript
    scripted_transcript: GameTranscript
    distance: int


def match_transcripts(
    llm_transcripts: list[GameTranscript],
    scripted_transcripts: list[GameTranscript],
    threshold: int = HAMMING_THRESHOLD,
) -> list[MatchedPair]:
    """Greedy one-to-one matching: for each LLM transcript, pair with the
    nearest unused scripted transcript within the threshold.

    Deterministic given the order of the LLM list (we sort by game_id first).
    """
    used_indices: set[int] = set()
    pairs: list[MatchedPair] = []

    llm_sorted = sorted(llm_transcripts, key=lambda t: t.game_id)

    for llm_t in llm_sorted:
        best_idx: int | None = None
        best_dist: int | None = None
        for i, scr_t in enumerate(scripted_transcripts):
            if i in used_indices:
                continue
            try:
                d = joint_hamming(llm_t, scr_t)
            except ValueError:
                continue
            if best_dist is None or d < best_dist:
                best_idx = i
                best_dist = d
        if best_idx is not None and best_dist is not None and best_dist <= threshold:
            pairs.append(
                MatchedPair(
                    llm_transcript=llm_t,
                    scripted_transcript=scripted_transcripts[best_idx],
                    distance=best_dist,
                )
            )
            used_indices.add(best_idx)

    return pairs
