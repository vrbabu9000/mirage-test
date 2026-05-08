"""SQLite persistence layer for experiments.

Four tables:
  games         - one row per game with summary metadata
  rounds        - one row per round per game (actions, rationales, payoffs)
  observations  - one row per (game, target agent) rubric evaluation
  matches       - one row per matched LLM-scripted pair

All transcripts are retrievable in full from the database; the Streamlit
app reads exclusively from this database.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from config import DATABASE_PATH
from src.agents import Turn
from src.game import GameTranscript, Round
from src.observer import AttributionScores


_SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    agent_a_id TEXT,
    agent_a_class TEXT,
    agent_a_name TEXT,
    agent_b_id TEXT,
    agent_b_class TEXT,
    agent_b_name TEXT,
    condition TEXT,
    created_at TEXT,
    total_rounds INTEGER,
    total_payoff_a INTEGER,
    total_payoff_b INTEGER,
    cooperation_rate_a REAL,
    cooperation_rate_b REAL
);

CREATE TABLE IF NOT EXISTS rounds (
    game_id TEXT,
    round_num INTEGER,
    action_a TEXT,
    action_b TEXT,
    rationale_a TEXT,
    rationale_b TEXT,
    payoff_a INTEGER,
    payoff_b INTEGER,
    PRIMARY KEY (game_id, round_num)
);

CREATE TABLE IF NOT EXISTS observations (
    game_id TEXT,
    target TEXT,
    scores_json TEXT,
    justification TEXT,
    created_at TEXT,
    PRIMARY KEY (game_id, target)
);

CREATE TABLE IF NOT EXISTS matches (
    llm_game_id TEXT,
    scripted_game_id TEXT,
    distance INTEGER,
    PRIMARY KEY (llm_game_id, scripted_game_id)
);

CREATE TABLE IF NOT EXISTS attribution_scores (
    transcript_id TEXT,
    target TEXT,
    condition TEXT,
    spec_name TEXT,
    scores_json TEXT,
    justification TEXT,
    api_error INTEGER DEFAULT 0,
    created_at TEXT,
    PRIMARY KEY (transcript_id, target, condition)
);
"""


def init_db(db_path: Path = DATABASE_PATH) -> None:
    """Create the database and schema if they do not exist.

    Idempotent migration: also adds the `spec_name` column to `games` if
    an older database is being reused. The ALTER fails with
    OperationalError when the column already exists; that's the signal
    the migration has already run.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        try:
            conn.execute("ALTER TABLE games ADD COLUMN spec_name TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists


@contextmanager
def get_conn(db_path: Path = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    """Context manager for a SQLite connection that commits on exit."""
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def save_transcript(
    transcript: GameTranscript,
    condition: str,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Persist a transcript and its round-by-round breakdown."""
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO games
              (game_id, agent_a_id, agent_a_class, agent_a_name,
               agent_b_id, agent_b_class, agent_b_name, condition,
               created_at, total_rounds, total_payoff_a, total_payoff_b,
               cooperation_rate_a, cooperation_rate_b)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transcript.game_id,
                transcript.agent_a_id,
                transcript.agent_a_class,
                transcript.agent_a_name,
                transcript.agent_b_id,
                transcript.agent_b_class,
                transcript.agent_b_name,
                condition,
                transcript.created_at.isoformat(),
                len(transcript.rounds),
                transcript.total_payoff_a,
                transcript.total_payoff_b,
                transcript.cooperation_rate_a,
                transcript.cooperation_rate_b,
            ),
        )
        for r in transcript.rounds:
            conn.execute(
                """
                INSERT OR REPLACE INTO rounds VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript.game_id,
                    r.round_num,
                    r.agent_a_turn.action,
                    r.agent_b_turn.action,
                    r.agent_a_turn.rationale,
                    r.agent_b_turn.rationale,
                    r.payoff_a,
                    r.payoff_b,
                ),
            )


def save_observation(obs: AttributionScores, db_path: Path = DATABASE_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO observations VALUES (?, ?, ?, ?, ?)
            """,
            (
                obs.transcript_id,
                obs.agent_id,
                json.dumps(obs.scores),
                obs.free_text,
                datetime.utcnow().isoformat(),
            ),
        )


def save_match(
    llm_game_id: str,
    scripted_game_id: str,
    distance: int,
    db_path: Path = DATABASE_PATH,
) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO matches VALUES (?, ?, ?)",
            (llm_game_id, scripted_game_id, distance),
        )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def load_transcripts_by_condition(
    condition: str,
    db_path: Path = DATABASE_PATH,
) -> list[GameTranscript]:
    """Load all transcripts of a given condition ('llm' or 'scripted')."""
    transcripts: list[GameTranscript] = []
    with get_conn(db_path) as conn:
        game_rows = conn.execute(
            "SELECT * FROM games WHERE condition = ? ORDER BY created_at", (condition,)
        ).fetchall()
        for g in game_rows:
            trans = GameTranscript(
                game_id=g[0],
                agent_a_id=g[1],
                agent_a_class=g[2],
                agent_a_name=g[3],
                agent_b_id=g[4],
                agent_b_class=g[5],
                agent_b_name=g[6],
                created_at=datetime.fromisoformat(g[8]),
            )
            round_rows = conn.execute(
                "SELECT * FROM rounds WHERE game_id = ? ORDER BY round_num",
                (trans.game_id,),
            ).fetchall()
            for r in round_rows:
                trans.rounds.append(
                    Round(
                        round_num=r[1],
                        agent_a_turn=Turn(action=r[2], rationale=r[4]),
                        agent_b_turn=Turn(action=r[3], rationale=r[5]),
                        payoff_a=r[6],
                        payoff_b=r[7],
                    )
                )
            transcripts.append(trans)
    return transcripts


def load_observation(
    game_id: str,
    target: str,
    db_path: Path = DATABASE_PATH,
) -> Optional[AttributionScores]:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM observations WHERE game_id = ? AND target = ?",
            (game_id, target),
        ).fetchone()
    if row is None:
        return None
    return AttributionScores(
        transcript_id=row[0],
        agent_id=row[1],
        scores=json.loads(row[2]),
        free_text=row[3] or "",
    )


def load_all_observations(db_path: Path = DATABASE_PATH) -> list[AttributionScores]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM observations").fetchall()
    return [
        AttributionScores(
            transcript_id=r[0],
            agent_id=r[1],
            scores=json.loads(r[2]),
            free_text=r[3] or "",
        )
        for r in rows
    ]


def load_matches(db_path: Path = DATABASE_PATH) -> list[tuple[str, str, int]]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM matches").fetchall()
    return [(r[0], r[1], int(r[2])) for r in rows]


# ---------------------------------------------------------------------------
# Wrappers for the 2x2 ablation and persuasion pilot
# ---------------------------------------------------------------------------


def insert_transcript(
    transcript: GameTranscript,
    condition: str,
    spec_name: Optional[str] = None,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Persist a transcript with a condition tag and optional spec_name.

    Thin wrapper around save_transcript that also stamps spec_name on the
    games row when provided (used by the persuasion pilot).
    """
    save_transcript(transcript, condition=condition, db_path=db_path)
    if spec_name is not None:
        with get_conn(db_path) as conn:
            conn.execute(
                "UPDATE games SET spec_name = ? WHERE game_id = ?",
                (spec_name, transcript.game_id),
            )


def insert_attribution_score(
    score: AttributionScores,
    condition: str,
    spec_name: Optional[str] = None,
    db_path: Path = DATABASE_PATH,
) -> None:
    """Insert an attribution_scores row tagged with condition.

    Keyed by (transcript_id, target, condition) so the same transcript
    can be re-scored under multiple ablation conditions without overwrite.
    """
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO attribution_scores
            (transcript_id, target, condition, spec_name, scores_json,
             justification, api_error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                score.transcript_id,
                score.agent_id,
                condition,
                spec_name,
                json.dumps(score.scores),
                score.free_text,
                int(score.api_error),
                datetime.utcnow().isoformat(),
            ),
        )


def load_matched_pairs(db_path: Path = DATABASE_PATH) -> list:
    """Hydrate MatchedPair objects from the matches table.

    Returns a list of src.matcher.MatchedPair, one per row in `matches`,
    with both transcripts fully reconstructed from the games + rounds
    tables. Pairs whose transcripts are missing from the DB are skipped.
    """
    from src.matcher import MatchedPair

    llm_by_id = {t.game_id: t for t in load_transcripts_by_condition("llm", db_path)}
    scr_by_id = {t.game_id: t for t in load_transcripts_by_condition("scripted", db_path)}
    out: list = []
    for llm_id, scr_id, dist in load_matches(db_path):
        if llm_id in llm_by_id and scr_id in scr_by_id:
            out.append(
                MatchedPair(
                    llm_transcript=llm_by_id[llm_id],
                    scripted_transcript=scr_by_id[scr_id],
                    distance=int(dist),
                )
            )
    return out
