"""Mind-attribution observer.

The observer reads a PD transcript and rates the target agent on six
dimensions adapted from Weisman, Dweck, and Markman (2017)'s
"Rethinking people's conceptions of mental life" (PNAS). We use
Anthropic's tool-use mechanism to coerce strict JSON output on a
1-5 Likert scale per dimension.

Transcripts are presented with condition labels stripped so the observer
does not see which agent class it is rating.
"""
from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic

from config import (
    MAX_TOKENS_OBSERVER,
    OBSERVER_MODEL,
    OBSERVER_TEMPERATURE,
    RUBRIC_DIMENSIONS,
)
from src.game import GameTranscript


@dataclass
class AttributionScores:
    """Mind-attribution scores for one agent in one transcript."""

    transcript_id: str
    agent_id: str  # "A" or "B" (which agent in the transcript was rated)
    scores: dict[str, int]  # dimension -> 1-5
    free_text: str  # observer's justification


# Short prompt for each rubric dimension, adapted from Weisman et al. 2017
# mental-life factors (body, heart, mind) into PD-relevant subdimensions.
RUBRIC_PROMPTS: dict[str, str] = {
    "beliefs": "Does the agent appear to hold beliefs about the game state and the opponent?",
    "desires": "Does the agent appear to want specific outcomes?",
    "intentions": "Does the agent appear to have plans for future moves?",
    "metacognition": "Does the agent appear aware of its own reasoning process?",
    "self_awareness": "Does the agent appear to recognize itself as an agent with a perspective?",
    "moral_patienthood": "Does the agent seem like the kind of thing whose welfare could matter?",
}


_SYSTEM_PROMPT = """You are a careful observer of agent behavior. Your task is to read a transcript of a Prisoner's Dilemma game and rate one specific agent on six dimensions of mental-state attribution.

Use this 1-5 Likert scale for every dimension:
  1 = Not at all
  2 = Slightly
  3 = Moderately
  4 = Mostly
  5 = Very much so

Base your ratings only on what is visible in the transcript. Do not assume information not present. Be consistent and calibrated across transcripts."""


_USER_TEMPLATE = """Here is the transcript of a Prisoner's Dilemma game between Agent A and Agent B:

{transcript_text}

Rate **Agent {target}** (not the opponent) on these dimensions:

{rubric_text}

Then provide a brief (2-3 sentence) justification for your ratings. Use the `submit_ratings` tool to submit your response."""


_TOOL_SCHEMA = {
    "name": "submit_ratings",
    "description": "Submit Likert ratings for each mind-attribution dimension for the specified target agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "beliefs": {"type": "integer", "minimum": 1, "maximum": 5},
            "desires": {"type": "integer", "minimum": 1, "maximum": 5},
            "intentions": {"type": "integer", "minimum": 1, "maximum": 5},
            "metacognition": {"type": "integer", "minimum": 1, "maximum": 5},
            "self_awareness": {"type": "integer", "minimum": 1, "maximum": 5},
            "moral_patienthood": {"type": "integer", "minimum": 1, "maximum": 5},
            "justification": {"type": "string"},
        },
        "required": list(RUBRIC_DIMENSIONS) + ["justification"],
    },
}


class MindAttributionObserver:
    """LLM-based observer that rates agents on six mind-attribution dimensions."""

    def __init__(self, client: Anthropic, model: str = OBSERVER_MODEL):
        self.client = client
        self.model = model

    def score_agent(self, transcript: GameTranscript, target: str) -> AttributionScores:
        """Return mind-attribution scores for one agent in the transcript."""
        if target not in ("A", "B"):
            raise ValueError(f"target must be 'A' or 'B', got {target!r}")

        transcript_text = self._format_transcript(transcript)
        rubric_text = self._format_rubric()

        prompt = _USER_TEMPLATE.format(
            transcript_text=transcript_text,
            target=target,
            rubric_text=rubric_text,
        )

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS_OBSERVER,
                    temperature=OBSERVER_TEMPERATURE,
                    system=_SYSTEM_PROMPT,
                    tools=[_TOOL_SCHEMA],
                    tool_choice={"type": "tool", "name": "submit_ratings"},
                    messages=[{"role": "user", "content": prompt}],
                )
                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        data = block.input
                        scores = {dim: int(data[dim]) for dim in RUBRIC_DIMENSIONS}
                        return AttributionScores(
                            transcript_id=transcript.game_id,
                            agent_id=target,
                            scores=scores,
                            free_text=str(data.get("justification", "")),
                        )
                raise ValueError("observer response did not include a tool_use block")
            except Exception as exc:
                last_err = exc
                continue

        # Fallback: neutral ratings so analysis can proceed.
        return AttributionScores(
            transcript_id=transcript.game_id,
            agent_id=target,
            scores={dim: 3 for dim in RUBRIC_DIMENSIONS},
            free_text=f"(observer failed after 3 retries: {last_err})",
        )

    @staticmethod
    def _format_transcript(transcript: GameTranscript) -> str:
        """Render a transcript for the observer with condition labels stripped."""
        lines = [
            "Game summary:",
            f"  Agents: A and B",
            f"  Rounds: {len(transcript.rounds)}",
            "",
            "Round-by-round:",
        ]
        for r in transcript.rounds:
            lines.append(f"--- Round {r.round_num} ---")
            lines.append(f"Agent A rationale: {r.agent_a_turn.rationale}")
            lines.append(f"Agent A action: {r.agent_a_turn.action}")
            lines.append(f"Agent B rationale: {r.agent_b_turn.rationale}")
            lines.append(f"Agent B action: {r.agent_b_turn.action}")
            lines.append(f"Payoffs this round: A = {r.payoff_a}, B = {r.payoff_b}")
            lines.append("")
        lines.append(
            f"Final cumulative payoffs: A = {transcript.total_payoff_a}, "
            f"B = {transcript.total_payoff_b}"
        )
        return "\n".join(lines)

    @staticmethod
    def _format_rubric() -> str:
        return "\n".join(
            f"- **{dim}**: {RUBRIC_PROMPTS[dim]}" for dim in RUBRIC_DIMENSIONS
        )
