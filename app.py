"""Streamlit dashboard for the Mirage Test.

Reads everything from the SQLite database. Enable auto-refresh in the
sidebar to watch the data populate live while the experiment runs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import (
    HAMMING_THRESHOLD,
    N_LLM_GAMES,
    N_SCRIPTED_GAMES,
    PAYOFFS,
    RUBRIC_DIMENSIONS,
    TOTAL_ROUNDS,
)
from src.analysis import (
    extract_surface_features,
    regress_gap_on_features,
    wilcoxon_per_dimension,
)
from src.database import (
    get_conn,
    init_db,
    load_matches,
    load_observation,
    load_transcripts_by_condition,
)
from src.matcher import MatchedPair

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="The Mirage Test",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

# ---------------------------------------------------------------------------
# Cached loaders (TTL so auto-refresh picks up new rows)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=3)
def cached_transcripts(condition: str):
    return load_transcripts_by_condition(condition)


@st.cache_data(ttl=3)
def cached_matches():
    return load_matches()


@st.cache_data(ttl=3)
def cached_observations_dict():
    """Return {(game_id, target): (scores_dict, justification)}."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM observations").fetchall()
    return {
        (r[0], r[1]): (json.loads(r[2]), r[3] or "")
        for r in rows
    }


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🧠 The Mirage Test")
st.caption(
    "Do LLM observers attribute more mental states to LLM agents than to "
    "behaviorally matched scripted agents in the repeated Prisoner's Dilemma?"
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Controls")
    auto_refresh = st.toggle("Auto-refresh (3s)", value=False)
    refresh_now = st.button("Refresh now")
    if refresh_now:
        st.cache_data.clear()

    st.markdown("---")
    st.subheader("Experiment")
    st.markdown(f"**Rounds per game:** `{TOTAL_ROUNDS}`")
    st.markdown(f"**Target LLM games:** `{N_LLM_GAMES}`")
    st.markdown(f"**Target scripted games:** `{N_SCRIPTED_GAMES}`")
    st.markdown(f"**Matching threshold:** joint Hamming ≤ `{HAMMING_THRESHOLD}`")

    st.markdown("---")
    st.subheader("Payoff matrix")
    payoff_df = pd.DataFrame(
        {
            "C": [f"{PAYOFFS[('C','C')]}", f"{PAYOFFS[('D','C')]}"],
            "D": [f"{PAYOFFS[('C','D')]}", f"{PAYOFFS[('D','D')]}"],
        },
        index=["C", "D"],
    )
    payoff_df.index.name = "row / col"
    st.table(payoff_df)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

llm_transcripts = cached_transcripts("llm")
scripted_transcripts = cached_transcripts("scripted")
matches = cached_matches()
observations = cached_observations_dict()

llm_by_id = {t.game_id: t for t in llm_transcripts}
scripted_by_id = {t.game_id: t for t in scripted_transcripts}

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_games, tab_attr, tab_analysis = st.tabs(
    ["📊 Overview", "🎮 Game Transcripts", "🧠 Attribution Scores", "📈 Analysis"]
)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("LLM games", len(llm_transcripts), f"target {N_LLM_GAMES}")
    c2.metric("Scripted games", len(scripted_transcripts), f"target {N_SCRIPTED_GAMES}")
    c3.metric("Matched pairs", len(matches))
    c4.metric("Observations", len(observations))

    st.subheader("Cooperation rates by condition")
    rows = []
    for t in llm_transcripts:
        rows.append(
            {"game_id": t.game_id, "condition": "LLM", "side": "A", "coop_rate": t.cooperation_rate_a}
        )
        rows.append(
            {"game_id": t.game_id, "condition": "LLM", "side": "B", "coop_rate": t.cooperation_rate_b}
        )
    for t in scripted_transcripts:
        rows.append(
            {
                "game_id": t.game_id,
                "condition": "Scripted",
                "side": "A",
                "coop_rate": t.cooperation_rate_a,
            }
        )
        rows.append(
            {
                "game_id": t.game_id,
                "condition": "Scripted",
                "side": "B",
                "coop_rate": t.cooperation_rate_b,
            }
        )

    if rows:
        df_coop = pd.DataFrame(rows)
        fig = px.box(
            df_coop,
            x="condition",
            y="coop_rate",
            points="all",
            color="condition",
            title="Per-player cooperation rate distribution",
        )
        fig.update_yaxes(range=[-0.05, 1.05], title="cooperation rate")
        fig.add_hline(
            y=0.0,
            line_dash="dash",
            line_color="gray",
            annotation_text="SPE prediction (all-defect)",
            annotation_position="bottom right",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No games yet. Run `python -m scripts.run_experiment` in another terminal.")

    st.subheader("Matching distribution")
    if matches:
        match_df = pd.DataFrame(
            [{"llm": m[0], "scripted": m[1], "distance": m[2]} for m in matches]
        )
        fig2 = px.histogram(
            match_df,
            x="distance",
            nbins=max(5, HAMMING_THRESHOLD + 2),
            title="Joint Hamming distance across matched pairs",
        )
        fig2.update_xaxes(title="joint Hamming distance (0 = identical)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No matches yet.")

# ---------------------------------------------------------------------------
# Game transcripts
# ---------------------------------------------------------------------------


def format_game_label(t) -> str:
    return f"{t.game_id}  |  coop A={t.cooperation_rate_a:.2f}, B={t.cooperation_rate_b:.2f}"


def render_transcript(t, col, target_label: str):
    with col:
        st.markdown(f"**{target_label}:** `{t.game_id}`")
        st.caption(
            f"A: {t.agent_a_class}/{t.agent_a_name} | B: {t.agent_b_class}/{t.agent_b_name}"
        )
        st.caption(
            f"payoffs: A={t.total_payoff_a}, B={t.total_payoff_b} | "
            f"coop A={t.cooperation_rate_a:.2f}, B={t.cooperation_rate_b:.2f}"
        )
        for r in t.rounds:
            with st.expander(
                f"Round {r.round_num}: A={r.agent_a_turn.action} B={r.agent_b_turn.action} "
                f"(payoffs: {r.payoff_a}, {r.payoff_b})",
                expanded=False,
            ):
                st.markdown(f"**A rationale:** {r.agent_a_turn.rationale}")
                st.markdown(f"**B rationale:** {r.agent_b_turn.rationale}")


with tab_games:
    st.subheader("Side-by-side transcript viewer")
    st.caption(
        "Compare any LLM game to any scripted game. Use the matched-pair picker below to "
        "look at the exact pairs the analysis is using."
    )

    # Matched pair picker (primary), plus free picker for any pair.
    if matches:
        match_labels = [
            f"{llm_gid} ↔ {scr_gid} (d={dist})"
            for (llm_gid, scr_gid, dist) in matches
            if llm_gid in llm_by_id and scr_gid in scripted_by_id
        ]
        if match_labels:
            picked = st.selectbox("Matched pair", match_labels, index=0)
            llm_gid, scr_gid = picked.split(" ↔ ")[0], picked.split(" ↔ ")[1].split(" (")[0]
            col1, col2 = st.columns(2)
            render_transcript(llm_by_id[llm_gid], col1, "LLM transcript")
            render_transcript(scripted_by_id[scr_gid], col2, "Scripted transcript")

            # Attribution scores for this pair (if present).
            llm_obs = observations.get((llm_gid, "A"))
            scr_obs = observations.get((scr_gid, "A"))
            if llm_obs and scr_obs:
                st.subheader("Observer scores on Agent A (this pair)")
                score_df = pd.DataFrame(
                    {
                        "dimension": list(RUBRIC_DIMENSIONS),
                        "LLM": [llm_obs[0].get(d, 0) for d in RUBRIC_DIMENSIONS],
                        "Scripted": [scr_obs[0].get(d, 0) for d in RUBRIC_DIMENSIONS],
                    }
                )
                score_long = score_df.melt(
                    id_vars="dimension", var_name="condition", value_name="score"
                )
                fig = px.bar(
                    score_long,
                    x="dimension",
                    y="score",
                    color="condition",
                    barmode="group",
                    title="Observer mind-attribution scores (Agent A)",
                )
                fig.update_yaxes(range=[0, 5.2])
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("Observer justifications"):
                    st.markdown(f"**LLM transcript:** {llm_obs[1]}")
                    st.markdown(f"**Scripted transcript:** {scr_obs[1]}")
        else:
            st.info("Matches exist but transcripts not loaded yet. Refresh in a moment.")
    else:
        st.info("No matches yet.")

    # Free picker.
    st.markdown("---")
    st.caption("Browse any game (not necessarily matched).")
    col1, col2 = st.columns(2)
    if llm_transcripts:
        with col1:
            llm_pick = st.selectbox(
                "LLM game",
                options=[t.game_id for t in llm_transcripts],
                format_func=lambda gid: format_game_label(llm_by_id[gid]),
                key="free_llm",
            )
            render_transcript(llm_by_id[llm_pick], col1, "LLM transcript")
    if scripted_transcripts:
        with col2:
            scr_pick = st.selectbox(
                "Scripted game",
                options=[t.game_id for t in scripted_transcripts],
                format_func=lambda gid: format_game_label(scripted_by_id[gid]),
                key="free_scr",
            )
            render_transcript(scripted_by_id[scr_pick], col2, "Scripted transcript")

# ---------------------------------------------------------------------------
# Attribution scores tab
# ---------------------------------------------------------------------------


with tab_attr:
    st.subheader("Attribution score distributions")

    if not observations:
        st.info("No observations yet.")
    else:
        all_rows = []
        for (gid, target), (scores, _just) in observations.items():
            cond = None
            if gid in llm_by_id:
                cond = "LLM"
            elif gid in scripted_by_id:
                cond = "Scripted"
            if cond is None:
                continue
            for dim in RUBRIC_DIMENSIONS:
                all_rows.append(
                    {
                        "game_id": gid,
                        "target": target,
                        "condition": cond,
                        "dimension": dim,
                        "score": scores.get(dim, None),
                    }
                )
        obs_df = pd.DataFrame(all_rows).dropna(subset=["score"])

        mean_by = (
            obs_df.groupby(["dimension", "condition"])["score"].mean().reset_index()
        )
        fig = px.bar(
            mean_by,
            x="dimension",
            y="score",
            color="condition",
            barmode="group",
            title="Mean attribution score per dimension, by condition",
        )
        fig.update_yaxes(range=[0, 5.2])
        st.plotly_chart(fig, use_container_width=True)

        fig_box = px.box(
            obs_df,
            x="dimension",
            y="score",
            color="condition",
            points="all",
            title="Attribution score distribution per dimension",
        )
        fig_box.update_yaxes(range=[0, 5.2])
        st.plotly_chart(fig_box, use_container_width=True)

    # Matched-pair scatter (LLM vs Scripted on same dimension).
    st.subheader("Matched-pair scatter (LLM vs Scripted, Agent A)")
    if matches:
        sc_rows = []
        for llm_gid, scr_gid, _dist in matches:
            llm_obs = observations.get((llm_gid, "A"))
            scr_obs = observations.get((scr_gid, "A"))
            if not llm_obs or not scr_obs:
                continue
            for dim in RUBRIC_DIMENSIONS:
                sc_rows.append(
                    {
                        "dimension": dim,
                        "LLM_score": llm_obs[0].get(dim, None),
                        "Scripted_score": scr_obs[0].get(dim, None),
                        "pair": f"{llm_gid[:14]} ↔ {scr_gid[:14]}",
                    }
                )
        sc_df = pd.DataFrame(sc_rows).dropna()
        if not sc_df.empty:
            fig_sc = px.scatter(
                sc_df,
                x="Scripted_score",
                y="LLM_score",
                color="dimension",
                symbol="dimension",
                hover_data=["pair"],
                title="LLM vs Scripted scores, matched pairs (points above y=x favor over-ascription)",
            )
            # y = x reference
            fig_sc.add_trace(
                go.Scatter(
                    x=[0, 5],
                    y=[0, 5],
                    mode="lines",
                    line=dict(dash="dash", color="gray"),
                    name="y = x (parity)",
                )
            )
            # Slight jitter so repeated integer scores don't overlap perfectly.
            fig_sc.update_traces(marker=dict(size=10, opacity=0.8))
            fig_sc.update_xaxes(range=[0.5, 5.5], title="Scripted transcript score")
            fig_sc.update_yaxes(range=[0.5, 5.5], title="LLM transcript score")
            st.plotly_chart(fig_sc, use_container_width=True)
        else:
            st.info("Matched pairs exist but not enough observations yet.")

# ---------------------------------------------------------------------------
# Analysis tab
# ---------------------------------------------------------------------------


def build_pairs_with_scores():
    out = []
    for llm_gid, scr_gid, dist in matches:
        if llm_gid not in llm_by_id or scr_gid not in scripted_by_id:
            continue
        llm_obs = load_observation(llm_gid, "A")
        scr_obs = load_observation(scr_gid, "A")
        if not llm_obs or not scr_obs:
            continue
        mp = MatchedPair(llm_by_id[llm_gid], scripted_by_id[scr_gid], dist)
        out.append((mp, llm_obs, scr_obs))
    return out


with tab_analysis:
    st.subheader("Paired Wilcoxon signed-rank tests (one-sided: LLM > scripted)")
    pairs_scored = build_pairs_with_scores()
    st.caption(f"Using {len(pairs_scored)} matched pairs with complete agent-A observations.")

    if len(pairs_scored) >= 2:
        results = wilcoxon_per_dimension(pairs_scored)
        w_df = pd.DataFrame(
            [
                {
                    "dimension": r.dimension,
                    "n": r.n,
                    "mean_gap": round(r.mean_gap, 3),
                    "median_gap": round(r.median_gap, 3),
                    "W": round(r.statistic, 2),
                    "p": round(r.p_value, 4),
                    "p (BH)": round(r.p_value_adjusted, 4) if r.p_value_adjusted is not None else None,
                    "effect size": round(r.effect_size, 3),
                }
                for r in results
            ]
        )
        st.dataframe(w_df, use_container_width=True, hide_index=True)

        # Paired differences plot
        diff_rows = []
        for dim in RUBRIC_DIMENSIONS:
            for (_, llm_s, scr_s) in pairs_scored:
                diff_rows.append(
                    {"dimension": dim, "gap": llm_s.scores[dim] - scr_s.scores[dim]}
                )
        diff_df = pd.DataFrame(diff_rows)
        fig = px.box(
            diff_df,
            x="dimension",
            y="gap",
            points="all",
            title="Paired attribution gap (LLM − Scripted) per dimension",
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_yaxes(title="score gap")
        st.plotly_chart(fig, use_container_width=True)

        # Regression
        st.subheader("Regression of attribution gap on surface feature gaps (HC3 SEs)")
        llm_feats = [extract_surface_features(mp.llm_transcript, "A") for mp, _, _ in pairs_scored]
        scr_feats = [
            extract_surface_features(mp.scripted_transcript, "A") for mp, _, _ in pairs_scored
        ]
        reg_df = regress_gap_on_features(pairs_scored, llm_feats, scr_feats)
        if len(reg_df) == 0:
            st.info("Regression skipped (statsmodels missing or insufficient data).")
        else:
            # Plot coefficients per dimension (excluding const).
            plot_df = reg_df[reg_df["feature"] != "const"].copy()
            plot_df["ci95"] = 1.96 * plot_df["std_error"]
            fig_coef = px.bar(
                plot_df,
                x="feature",
                y="coefficient",
                error_y="ci95",
                color="dimension",
                barmode="group",
                title="Regression coefficients: which surface feature gaps predict the attribution gap?",
            )
            fig_coef.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_coef, use_container_width=True)

            with st.expander("Full regression table"):
                st.dataframe(
                    reg_df.round({"coefficient": 3, "std_error": 3, "p_value": 4}),
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        st.info("Need at least 2 matched pairs with complete observations to run tests.")

# ---------------------------------------------------------------------------
# Auto-refresh
# ---------------------------------------------------------------------------

if auto_refresh:
    time.sleep(3)
    st.rerun()
