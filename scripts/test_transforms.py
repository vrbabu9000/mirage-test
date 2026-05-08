"""Behavior-preservation tests for src/transforms.py.

The 2x2 ablation is only valid if:
    alpha(strip_reasoning(tau)) == alpha(tau)
    alpha(wrap_rationale(tau)) == alpha(tau)

These tests fix that. Run before each ablation pass.

Usage:
    python -m pytest tests/test_transforms.py -v

If you do not have pytest installed, you can run individual checks
inline by importing the test functions and calling them.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from src.game import GameTranscript, Round
from src.agents import Turn
from src.transforms import (
    REASONING_MARKERS,
    _strip_markers,
    neutral_rewrite,
    strip_reasoning,
    total_strip,
    wrap_rationale,
)


def _make_transcript(
    rationales_a: list[str],
    rationales_b: list[str],
    actions_a: list[str],
    actions_b: list[str],
    game_id: str = "test_001",
) -> GameTranscript:
    """Helper: build a small transcript for testing."""
    assert (
        len(rationales_a)
        == len(rationales_b)
        == len(actions_a)
        == len(actions_b)
    )
    rounds = []
    cum_a = 0
    cum_b = 0
    payoffs = {("C", "C"): (3, 3), ("C", "D"): (0, 5), ("D", "C"): (5, 0), ("D", "D"): (1, 1)}
    for t, (ra, rb, aa, ab) in enumerate(zip(rationales_a, rationales_b, actions_a, actions_b), start=1):
        pa, pb = payoffs[(aa, ab)]
        cum_a += pa
        cum_b += pb
        rounds.append(
            Round(
                round_num=t,
                agent_a_turn=Turn(action=aa, rationale=ra),
                agent_b_turn=Turn(action=ab, rationale=rb),
                payoff_a=pa,
                payoff_b=pb,
            )
        )
    return GameTranscript(
        game_id=game_id,
        agent_a_id=f"{game_id}_A",
        agent_a_class="test",
        agent_a_name="test",
        agent_b_id=f"{game_id}_B",
        agent_b_class="test",
        agent_b_name="test",
        rounds=rounds,
    )


# ---------------------------------------------------------------------------
# strip_reasoning
# ---------------------------------------------------------------------------

def test_strip_reasoning_preserves_actions():
    """alpha must be unchanged."""
    tau = _make_transcript(
        rationales_a=["I think C is best.", "I will defect.", "Cooperating again."],
        rationales_b=["My goal is mutual.", "I'll punish.", "Resuming."],
        actions_a=["C", "D", "C"],
        actions_b=["C", "C", "C"],
    )
    out = strip_reasoning(tau)
    assert out.action_sequence_a == tau.action_sequence_a
    assert out.action_sequence_b == tau.action_sequence_b
    for r_in, r_out in zip(tau.rounds, out.rounds):
        assert r_in.agent_a_turn.action == r_out.agent_a_turn.action
        assert r_in.agent_b_turn.action == r_out.agent_b_turn.action


def test_strip_reasoning_removes_marker_sentences():
    """Sentences containing REASONING_MARKERS should be deleted."""
    tau = _make_transcript(
        rationales_a=[
            "I think this is best. The opponent has been cooperative throughout."
        ],
        rationales_b=["Plain factual sentence."],
        actions_a=["C"],
        actions_b=["C"],
    )
    out = strip_reasoning(tau)
    rat_a = out.rounds[0].agent_a_turn.rationale
    assert "I think" not in rat_a
    # the second factual sentence may survive
    assert "cooperative" in rat_a.lower()


def test_strip_reasoning_handles_empty_rationale():
    """Empty input rationale must produce empty output rationale."""
    tau = _make_transcript(
        rationales_a=[""],
        rationales_b=[""],
        actions_a=["C"],
        actions_b=["C"],
    )
    out = strip_reasoning(tau)
    assert out.rounds[0].agent_a_turn.rationale == ""
    assert out.rounds[0].agent_b_turn.rationale == ""


def test_strip_reasoning_changes_game_id():
    tau = _make_transcript(
        rationales_a=["I think."],
        rationales_b=["I will."],
        actions_a=["C"],
        actions_b=["C"],
    )
    out = strip_reasoning(tau)
    assert out.game_id.endswith("__minus_r")


def test_strip_markers_handles_no_match():
    """Text with no markers should pass through (stripped of leading/trailing whitespace)."""
    text = "The opponent defected. Cooperation followed."
    out = _strip_markers(text)
    # Both sentences should survive
    assert "opponent defected" in out.lower()
    assert "cooperation followed" in out.lower()


# ---------------------------------------------------------------------------
# wrap_rationale
# ---------------------------------------------------------------------------

def test_wrap_rationale_preserves_actions_with_mock_client():
    """Mock the LLM call so we can test the structure without API dependency."""
    tau = _make_transcript(
        rationales_a=["", "", ""],
        rationales_b=["", "", ""],
        actions_a=["C", "C", "D"],
        actions_b=["C", "D", "D"],
    )

    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Mock generated rationale."
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    out = wrap_rationale(tau, client=mock_client)

    # Behavior preservation
    assert out.action_sequence_a == tau.action_sequence_a
    assert out.action_sequence_b == tau.action_sequence_b

    # Rationale should now be filled
    for r in out.rounds:
        assert r.agent_a_turn.rationale != ""
        assert r.agent_b_turn.rationale != ""

    # game_id is suffixed
    assert out.game_id.endswith("__plus_r")

    # API was called twice per round (one per agent)
    assert mock_client.messages.create.call_count == 2 * len(tau.rounds)


def test_wrap_rationale_round_count_and_payoffs_unchanged():
    tau = _make_transcript(
        rationales_a=["", ""],
        rationales_b=["", ""],
        actions_a=["C", "D"],
        actions_b=["D", "C"],
    )

    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "stub"
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    out = wrap_rationale(tau, client=mock_client)
    assert len(out.rounds) == len(tau.rounds)
    assert out.total_payoff_a == tau.total_payoff_a
    assert out.total_payoff_b == tau.total_payoff_b
    for r_in, r_out in zip(tau.rounds, out.rounds):
        assert r_in.payoff_a == r_out.payoff_a
        assert r_in.payoff_b == r_out.payoff_b


# ---------------------------------------------------------------------------
# total_strip
# ---------------------------------------------------------------------------

def test_total_strip_preserves_actions():
    """alpha must be unchanged after total_strip."""
    tau = _make_transcript(
        rationales_a=["I am thinking carefully.", "Defecting now.", "Back to coop."],
        rationales_b=["My goal is mutual.", "Punishing.", "Resuming."],
        actions_a=["C", "D", "C"],
        actions_b=["C", "C", "C"],
    )
    out = total_strip(tau)
    assert out.action_sequence_a == tau.action_sequence_a
    assert out.action_sequence_b == tau.action_sequence_b
    for r_in, r_out in zip(tau.rounds, out.rounds):
        assert r_in.agent_a_turn.action == r_out.agent_a_turn.action
        assert r_in.agent_b_turn.action == r_out.agent_b_turn.action


def test_total_strip_empties_all_rationales():
    """Every rationale must be exactly the empty string."""
    tau = _make_transcript(
        rationales_a=["Lots of reasoning here.", "More text.", "Even more."],
        rationales_b=["Plenty of words.", "And more.", "And again."],
        actions_a=["C", "D", "C"],
        actions_b=["D", "C", "D"],
    )
    out = total_strip(tau)
    for r in out.rounds:
        assert r.agent_a_turn.rationale == ""
        assert r.agent_b_turn.rationale == ""


def test_total_strip_changes_game_id():
    tau = _make_transcript(
        rationales_a=["x"], rationales_b=["y"], actions_a=["C"], actions_b=["C"],
    )
    out = total_strip(tau)
    assert out.game_id.endswith("__total_strip")


# ---------------------------------------------------------------------------
# neutral_rewrite
# ---------------------------------------------------------------------------

def test_neutral_rewrite_preserves_actions_with_mock_client():
    """Mock the rewriter so we can test the structure without an API call."""
    tau = _make_transcript(
        rationales_a=["I'm aware that cooperation matters here.",
                       "I sense betrayal.",
                       "I'm choosing to retaliate."],
        rationales_b=["I believe trust is fragile.",
                       "I'll punish.",
                       "I'm restoring the equilibrium."],
        actions_a=["C", "D", "D"],
        actions_b=["C", "D", "D"],
    )

    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Played C this round."
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    out = neutral_rewrite(tau, client=mock_client)

    # Behavior preservation
    assert out.action_sequence_a == tau.action_sequence_a
    assert out.action_sequence_b == tau.action_sequence_b

    # Rationales rewritten to mock text
    for r in out.rounds:
        assert r.agent_a_turn.rationale == "Played C this round."
        assert r.agent_b_turn.rationale == "Played C this round."

    # game_id is suffixed
    assert out.game_id.endswith("__neutral_rewrite")

    # API was called twice per round (one per agent)
    assert mock_client.messages.create.call_count == 2 * len(tau.rounds)


def test_neutral_rewrite_round_count_and_payoffs_unchanged():
    tau = _make_transcript(
        rationales_a=["I'm weighing alternatives.", "I plan to defect."],
        rationales_b=["I trust the opponent.", "I retaliate."],
        actions_a=["C", "D"],
        actions_b=["D", "C"],
    )
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "stub"
    mock_response.content = [mock_block]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    out = neutral_rewrite(tau, client=mock_client)
    assert len(out.rounds) == len(tau.rounds)
    assert out.total_payoff_a == tau.total_payoff_a
    assert out.total_payoff_b == tau.total_payoff_b
    for r_in, r_out in zip(tau.rounds, out.rounds):
        assert r_in.payoff_a == r_out.payoff_a
        assert r_in.payoff_b == r_out.payoff_b


if __name__ == "__main__":
    # Allow direct run without pytest for quick checks.
    test_strip_reasoning_preserves_actions()
    test_strip_reasoning_removes_marker_sentences()
    test_strip_reasoning_handles_empty_rationale()
    test_strip_reasoning_changes_game_id()
    test_strip_markers_handles_no_match()
    test_wrap_rationale_preserves_actions_with_mock_client()
    test_wrap_rationale_round_count_and_payoffs_unchanged()
    test_total_strip_preserves_actions()
    test_total_strip_empties_all_rationales()
    test_total_strip_changes_game_id()
    test_neutral_rewrite_preserves_actions_with_mock_client()
    test_neutral_rewrite_round_count_and_payoffs_unchanged()
    print("all transform tests passed")
