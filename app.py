from __future__ import annotations

import html
import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from boilerroom_tool.ask import answer_question
from boilerroom_tool.settings import PEAKS_DIR, SCORES_DIR, SET_SUMMARY_PATH, TRACKS_DIR, TRENDING_DJ_PATH


NEON_CYAN = "#006B4F"
NEON_MAGENTA = "#B01875"
ACID_GREEN = "#258A45"
ACID_YELLOW = "#A06A00"
HOT_PINK = "#C2415D"
INK = "#151A1C"
MUTED = "#4D5654"
PANEL = "#FFFFFF"
PLOT_COLORS = [NEON_CYAN, NEON_MAGENTA, "#1F75B6", ACID_YELLOW, "#6E3FA3", HOT_PINK, "#267A8A"]


def canonical_track(track_name: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9]+", " ", str(track_name).lower()).strip()
    return re.sub(r"\s+", " ", key)


def inject_theme_css() -> None:
    st.markdown(
        """
<style>
:root {
  --bg: #05070d;
  --panel: rgba(8, 14, 28, 0.90);
  --panel-2: rgba(13, 20, 38, 0.78);
  --ink: #f2f7ff;
  --muted: #8b9ab4;
  --cyan: #32e6ef;
  --magenta: #d83aa8;
  --acid: #9fe879;
  --yellow: #d7f56a;
  --hot: #e45a8b;
}

.stApp {
  background:
    radial-gradient(circle at 86% 8%, rgba(50, 230, 239, 0.10), transparent 30%),
    radial-gradient(circle at 6% 18%, rgba(216, 58, 168, 0.08), transparent 30%),
    linear-gradient(180deg, #05070d 0%, #07101d 52%, #03050a 100%);
  color: var(--ink);
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 24px),
    linear-gradient(90deg, transparent 0 9%, rgba(50,230,239,0.08) 9% 9.25%, transparent 9.25% 100%),
    linear-gradient(90deg, transparent 0 86%, rgba(216,58,168,0.06) 86% 86.30%, transparent 86.30% 100%);
  mix-blend-mode: screen;
}

.stApp::after {
  content: "0110  FRAME  ENERGY  SIGNAL  CROWD  AUDIO  10SEC";
  position: fixed;
  right: 3rem;
  top: 8.4rem;
  width: 34rem;
  color: rgba(50, 230, 239, 0.08);
  font-family: "Aptos Mono", monospace;
  font-size: 0.75rem;
  letter-spacing: 0.18em;
  pointer-events: none;
  z-index: 0;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
  background: transparent !important;
}

.block-container {
  position: relative;
  z-index: 1;
  max-width: 1240px;
  padding-top: 3.2rem;
  padding-bottom: 4rem;
}

h1, h2, h3, label, .stMarkdown, .stCaption, p, span, div {
  color: var(--ink);
}

h1, h2, h3 {
  letter-spacing: -0.04em;
}

.glitch-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(120, 151, 186, 0.56);
  border-left: 4px solid var(--cyan);
  border-radius: 0;
  padding: 2.1rem 2.35rem;
  margin-bottom: 1.35rem;
  background:
    linear-gradient(135deg, rgba(6, 11, 22, 0.97), rgba(10, 16, 31, 0.90)),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0 1px, transparent 1px 20px);
  box-shadow: inset 0 0 0 1px rgba(50, 230, 239, 0.08);
}

.glitch-hero::before,
.glitch-hero::after {
  content: "";
  position: absolute;
  height: 4px;
  background: var(--magenta);
  opacity: 0.78;
}
.glitch-hero::before { width: 170px; right: 80px; top: 44px; }
.glitch-hero::after { width: 260px; right: 170px; bottom: 72px; background: var(--cyan); opacity: 0.35; }

.kicker {
  font-family: "Aptos Mono", monospace;
  color: var(--cyan);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-bottom: 0.55rem;
}

.glitch-title {
  position: relative;
  max-width: 860px;
  color: var(--ink);
  font-family: "Aptos Display", "Arial Black", sans-serif;
  font-size: clamp(2.55rem, 6vw, 5.1rem);
  font-weight: 900;
  line-height: 0.92;
  letter-spacing: -0.065em;
  text-shadow:
    -2px 2px 0 rgba(216, 58, 168, 0.74),
    2px -1px 0 rgba(50, 230, 239, 0.66);
}

.hero-copy {
  max-width: 720px;
  color: #c7d4e8;
  font-size: 1.12rem;
  line-height: 1.55;
  margin-top: 1.15rem;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1.35rem;
}

.signal-tag {
  border: 1px solid rgba(50, 230, 239, 0.44);
  color: #d9fbff;
  background: rgba(50, 230, 239, 0.045);
  border-radius: 0;
  padding: 0.38rem 0.72rem;
  font-family: "Aptos Mono", monospace;
  font-size: 0.74rem;
  letter-spacing: 0.08em;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin: 2.4rem 0 0.85rem;
}

.section-chip {
  width: 72px;
  height: 3px;
  background: linear-gradient(90deg, var(--magenta), var(--cyan));
  box-shadow: none;
}

.section-title {
  font-family: "Aptos Mono", monospace;
  color: var(--cyan);
  font-size: 0.92rem;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1.05rem;
  margin: 1rem 0 1.35rem;
}

.stat-card,
.decoder-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(120, 151, 186, 0.52);
  border-radius: 0;
  background: var(--panel);
  padding: 1rem 1.08rem;
  box-shadow: inset 0 0 0 1px rgba(50, 230, 239, 0.05);
}

.stat-card::before,
.decoder-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--cyan), var(--magenta), var(--acid));
}

.stat-label,
.decoder-label {
  color: var(--muted);
  font-family: "Aptos Mono", monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stat-value {
  color: var(--cyan);
  font-family: "Aptos Display", sans-serif;
  font-size: 2rem;
  font-weight: 900;
  line-height: 1;
  margin: 0.55rem 0 0.4rem;
}

.stat-note,
.decoder-body {
  color: #c8d2e5;
  font-size: 0.9rem;
  line-height: 1.35;
}

.decoder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin: 0.6rem 0 1.4rem;
}

.decoder-card strong {
  color: var(--ink);
}

.stSelectbox, .stMultiSelect, .stTextInput, .stSlider, .stCheckbox {
  color: var(--ink);
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea,
input {
  background: rgba(9, 14, 29, 0.96) !important;
  border-color: rgba(33, 246, 255, 0.46) !important;
  border-radius: 0 !important;
  color: var(--ink) !important;
  box-shadow: none !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
div[data-baseweb="input"] input {
  color: var(--ink) !important;
}

div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
ul[role="listbox"] {
  background: rgba(6, 10, 22, 0.98) !important;
  border: 1px solid rgba(50, 230, 239, 0.48) !important;
  border-radius: 0 !important;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.36) !important;
}

div[data-baseweb="popover"] *,
ul[role="listbox"] *,
li[role="option"],
div[role="option"] {
  color: #f2f7ff !important;
}

li[role="option"],
div[role="option"] {
  background: rgba(6, 10, 22, 0.98) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
}

ul[role="listbox"] li,
ul[role="listbox"] li > div,
ul[role="listbox"] div[role="option"],
ul[role="listbox"] div[role="option"] > div {
  background: rgba(6, 10, 22, 0.98) !important;
  color: #f2f7ff !important;
}

li[role="option"]:hover,
div[role="option"]:hover,
li[role="option"][aria-selected="true"],
div[role="option"][aria-selected="true"] {
  background: linear-gradient(90deg, rgba(33, 246, 255, 0.22), rgba(255, 42, 195, 0.14)) !important;
  color: #ffffff !important;
}

ul[role="listbox"] li:hover,
ul[role="listbox"] li:hover > div,
ul[role="listbox"] li[aria-selected="true"],
ul[role="listbox"] li[aria-selected="true"] > div,
ul[role="listbox"] div[role="option"]:hover,
ul[role="listbox"] div[role="option"]:hover > div,
ul[role="listbox"] div[role="option"][aria-selected="true"],
ul[role="listbox"] div[role="option"][aria-selected="true"] > div {
  background: linear-gradient(90deg, rgba(33, 246, 255, 0.24), rgba(255, 42, 195, 0.16)) !important;
  color: #ffffff !important;
  box-shadow: inset 4px 0 0 var(--cyan) !important;
}

ul[role="listbox"] li[aria-selected="true"] *,
ul[role="listbox"] div[role="option"][aria-selected="true"] * {
  color: #06101d !important;
  font-weight: 800 !important;
  text-shadow: none !important;
}

[data-testid="stCodeBlock"] pre,
code {
  border: 1px solid rgba(33, 246, 255, 0.36) !important;
  background: rgba(3, 5, 10, 0.94) !important;
  color: #dffbff !important;
}

[data-testid="stCodeBlock"],
[data-testid="stCodeBlock"] div {
  background: rgba(3, 5, 10, 0.94) !important;
  color: #dffbff !important;
}

[data-testid="stDataFrame"] {
  border: 1px solid rgba(33, 246, 255, 0.35);
  border-radius: 0;
  overflow: hidden;
  box-shadow: none;
}

.table-shell {
  width: 100%;
  overflow-x: auto;
  border: 1px solid rgba(120, 151, 186, 0.42);
  border-radius: 0;
  background: rgba(7, 11, 24, 0.88);
  box-shadow: none;
}

.glitch-table {
  width: 100%;
  border-collapse: collapse;
  color: var(--ink);
  font-size: 0.88rem;
}

.glitch-table thead th {
  position: sticky;
  top: 0;
  background: linear-gradient(90deg, rgba(33, 246, 255, 0.18), rgba(255, 42, 195, 0.14));
  color: #dffbff;
  font-family: "Aptos Mono", monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: left;
  padding: 0.8rem 0.9rem;
  border-bottom: 1px solid rgba(33, 246, 255, 0.38);
}

.glitch-table tbody td {
  padding: 0.72rem 0.9rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  color: #cbd8ec;
  vertical-align: top;
}

.glitch-table tbody tr:nth-child(even) td {
  background: rgba(255,255,255,0.025);
}

.glitch-table tbody tr:hover td {
  background: rgba(33, 246, 255, 0.07);
  color: var(--ink);
}

[data-testid="stExpander"] {
  border: 1px solid rgba(33, 246, 255, 0.30) !important;
  background: rgba(10, 14, 30, 0.68) !important;
  border-radius: 0 !important;
}

.stAlert {
  background: rgba(255, 47, 122, 0.12);
  border: 1px solid rgba(255, 47, 122, 0.45);
}

/* Clean professional product-docs theme override */
:root {
  --bg: #f7f8f5;
  --panel: #ffffff;
  --panel-2: #f1f4ef;
  --ink: #151a1c;
  --muted: #4d5654;
  --cyan: #006b4f;
  --magenta: #b01875;
  --acid: #258a45;
  --yellow: #a06a00;
  --hot: #c2415d;
  --border: #c9d2cc;
  --border-strong: #8f9c95;
}

.stApp {
  background: var(--bg) !important;
  color: var(--ink) !important;
}

.stApp::before,
.stApp::after {
  display: none !important;
  content: none !important;
}

.block-container {
  max-width: 1180px;
  padding-top: 2.1rem;
}

h1, h2, h3, h4, label, .stMarkdown, .stCaption, p, span, div {
  color: var(--ink);
}

.glitch-hero {
  border: 1px solid var(--border-strong);
  border-left: 5px solid var(--cyan);
  background: #ffffff;
  box-shadow: none;
  padding: 2rem 2.25rem 1.6rem;
}

.glitch-hero::before {
  width: 190px;
  height: 4px;
  right: 2rem;
  top: 1.25rem;
  background: var(--cyan);
  opacity: 1;
}

.glitch-hero::after {
  width: 260px;
  height: 2px;
  right: 2rem;
  bottom: 2rem;
  background: var(--border-strong);
  opacity: 1;
}

.kicker {
  color: var(--cyan);
  font-size: 0.78rem;
  letter-spacing: 0.16em;
}

.glitch-title {
  max-width: 820px;
  color: var(--ink);
  font-family: "Aptos Display", "Aptos", sans-serif;
  font-size: clamp(2.55rem, 5.2vw, 4.55rem);
  font-weight: 650;
  line-height: 1.04;
  letter-spacing: -0.045em;
  text-shadow: none;
}

.hero-copy {
  color: #2E3734;
  font-size: 1.04rem;
  line-height: 1.62;
}

.signal-tag {
  border: 1px solid var(--border-strong);
  color: var(--ink);
  background: #ffffff;
  font-size: 0.72rem;
}

.signal-tag:hover {
  border-color: var(--cyan);
  color: var(--cyan);
}

.section-head {
  gap: 0.8rem;
  margin: 2.15rem 0 0.8rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.55rem;
}

.section-chip {
  width: 46px;
  height: 3px;
  background: var(--cyan);
}

.section-title {
  color: var(--ink);
  font-size: 0.86rem;
  letter-spacing: 0.12em;
}

.stat-card,
.decoder-card {
  border: 1px solid var(--border-strong);
  background: #ffffff;
  box-shadow: none;
  padding: 1.05rem 1.1rem;
}

.stat-card::before,
.decoder-card::before {
  height: 3px;
  background: var(--cyan);
}

.stat-label,
.decoder-label {
  color: var(--cyan);
  font-size: 0.72rem;
}

.stat-value {
  color: var(--ink);
  font-weight: 650;
}

.stat-note,
.decoder-body {
  color: #4f5856;
  font-size: 0.92rem;
}

.decoder-card strong {
  color: var(--ink);
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea,
input {
  background: #ffffff !important;
  border-color: var(--border-strong) !important;
  color: var(--ink) !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
div[data-baseweb="input"] input {
  color: var(--ink) !important;
}

div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
ul[role="listbox"] {
  background: #ffffff !important;
  border: 1px solid var(--border-strong) !important;
  box-shadow: 0 14px 32px rgba(32, 36, 38, 0.14) !important;
}

div[data-baseweb="popover"] *,
ul[role="listbox"] *,
li[role="option"],
div[role="option"] {
  color: var(--ink) !important;
}

li[role="option"],
div[role="option"],
ul[role="listbox"] li,
ul[role="listbox"] li > div,
ul[role="listbox"] div[role="option"],
ul[role="listbox"] div[role="option"] > div {
  background: #ffffff !important;
  color: var(--ink) !important;
  border-bottom: 1px solid #DDE5E0 !important;
}

li[role="option"]:hover,
div[role="option"]:hover,
li[role="option"][aria-selected="true"],
div[role="option"][aria-selected="true"],
ul[role="listbox"] li:hover,
ul[role="listbox"] li:hover > div,
ul[role="listbox"] li[aria-selected="true"],
ul[role="listbox"] li[aria-selected="true"] > div,
ul[role="listbox"] div[role="option"]:hover,
ul[role="listbox"] div[role="option"]:hover > div,
ul[role="listbox"] div[role="option"][aria-selected="true"],
ul[role="listbox"] div[role="option"][aria-selected="true"] > div {
  background: #e8eee9 !important;
  color: var(--ink) !important;
  box-shadow: inset 4px 0 0 var(--cyan) !important;
}

ul[role="listbox"] li[aria-selected="true"] *,
ul[role="listbox"] div[role="option"][aria-selected="true"] * {
  color: var(--ink) !important;
  font-weight: 700 !important;
}

[data-testid="stCodeBlock"],
[data-testid="stCodeBlock"] div,
[data-testid="stCodeBlock"] pre,
code {
  background: #f0f3ef !important;
  color: var(--ink) !important;
  border-color: var(--border) !important;
}

[data-testid="stExpander"] {
  border: 1px solid var(--border-strong) !important;
  background: #ffffff !important;
}

.table-shell {
  border: 1px solid var(--border-strong);
  background: #ffffff;
}

.glitch-table {
  color: var(--ink);
}

.glitch-table thead th {
  background: #eef2ef;
  color: var(--ink);
  border-bottom: 1px solid var(--border-strong);
}

.glitch-table tbody td {
  color: #3f4846;
  border-bottom: 1px solid #edf0ed;
}

.glitch-table tbody tr:nth-child(even) td {
  background: #fafbf9;
}

.glitch-table tbody tr:hover td {
  background: #eef4ef;
  color: var(--ink);
}

.stAlert {
  background: #fff8e8;
  border: 1px solid #dfc98a;
}

.product-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.1rem;
  padding: 0.35rem 0 1rem;
  border-bottom: 1px solid var(--border);
}

.product-brand {
  display: flex;
  align-items: baseline;
  gap: 0.55rem;
  color: var(--ink);
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.product-brand span {
  color: var(--muted);
  font-weight: 400;
}

.product-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.product-nav a {
  color: var(--muted) !important;
  text-decoration: none;
}

.product-nav a:first-child {
  color: var(--cyan) !important;
  font-weight: 700;
}

@media (max-width: 900px) {
  .glitch-hero {
    padding: 1.55rem;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
<div class="glitch-hero">
  <div class="kicker">CrowdPulse // Boiler Room Crowd Analytics</div>
  <div class="glitch-title">Quantifying crowd emotion beyond text</div>
  <div class="hero-copy">
    A laptop-friendly signal lab for ranking DJ sets, scoring crowd energy every 10 seconds,
    and mapping the highest/lowest moments back to songs.
  </div>
  <div class="tag-row">
    <span class="signal-tag">YOUTUBE + REDDIT FUNNEL</span>
    <span class="signal-tag">VIDEO SIGNALS</span>
    <span class="signal-tag">TRACK ID</span>
    <span class="signal-tag">NATURAL LANGUAGE OPS</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        """
<div class="product-topbar">
  <div class="product-brand">CrowdPulse <span>/ Crowd Analytics</span></div>
  <nav class="product-nav" aria-label="Dashboard sections">
    <a>Overview</a>
    <a>Discovery</a>
    <a>Benchmarks</a>
    <a>Timeline</a>
    <a>Tracks</a>
  </nav>
</div>
""",
        unsafe_allow_html=True,
    )


def render_section(title: str) -> None:
    st.markdown(
        f"""
<div class="section-head">
  <div class="section-chip"></div>
  <div class="section-title">{html.escape(title)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_stat_grid(stats: list[tuple[str, str, str]]) -> None:
    cards = []
    for label, value, note in stats:
        cards.append(
            f"""
<div class="stat-card">
  <div class="stat-label">{html.escape(label)}</div>
  <div class="stat-value">{html.escape(value)}</div>
  <div class="stat-note">{html.escape(note)}</div>
</div>
"""
        )
    st.markdown(f"<div class=\"stat-grid\">{''.join(cards)}</div>", unsafe_allow_html=True)


def render_decoder_cards() -> None:
    cards = [
        (
            "Top Funnel",
            "YouTube and Reddit signals rank which DJs/sets should be pulled into the analysis queue first.",
        ),
        (
            "Crowd Energy",
            "Movement, phone-screen proxy, lighting flux, motion change, texture, and face presence are normalized into an engagement score.",
        ),
        (
            "Songs at Peaks",
            "Peak/low moments are mapped to tracks using chapters, timestamped descriptions, fingerprints, and manual overrides.",
        ),
    ]
    body = []
    for label, text in cards:
        body.append(
            f"""
<div class="decoder-card">
  <div class="decoder-label">{html.escape(label)}</div>
  <div class="decoder-body"><strong>{html.escape(text.split()[0])}</strong> {' '.join(html.escape(w) for w in text.split()[1:])}</div>
</div>
"""
        )
    st.markdown(f"<div class=\"decoder-grid\">{''.join(body)}</div>", unsafe_allow_html=True)


def count_track_rows() -> int:
    total = 0
    for path in TRACKS_DIR.glob("set_*_tracks.csv"):
        try:
            total += len(pd.read_csv(path))
        except Exception:
            continue
    return total


def render_dark_table(df: pd.DataFrame, max_rows: int | None = None) -> None:
    display_df = df.head(max_rows).copy() if max_rows else df.copy()
    for col in display_df.select_dtypes(include=["float"]).columns:
        display_df[col] = display_df[col].map(lambda value: f"{value:.3f}")
    table = display_df.to_html(index=False, classes="glitch-table", border=0, escape=True)
    st.markdown(f"<div class=\"table-shell\">{table}</div>", unsafe_allow_html=True)


def style_plotly(fig, height: int = 440):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(247, 248, 245, 0)",
        plot_bgcolor="#FFFFFF",
        font={"color": INK, "family": "Aptos, sans-serif"},
        title={"font": {"color": INK, "size": 22, "family": "Aptos Display, sans-serif"}},
        legend={
            "orientation": "h",
            "x": 0,
            "y": -0.34,
            "xanchor": "left",
            "yanchor": "top",
            "bgcolor": "rgba(247, 248, 245, 0)",
            "bordercolor": "#B8C3BC",
            "font": {"color": "#252B2D"},
        },
        margin={"l": 48, "r": 28, "t": 70, "b": 128},
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#D6DED8",
        zeroline=False,
        tickfont={"color": "#343C3A"},
        title_font={"color": INK},
        linecolor="#9AA79F",
        mirror=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E1E7E2",
        zeroline=False,
        tickfont={"color": "#343C3A"},
        title_font={"color": INK},
        linecolor="#9AA79F",
        mirror=True,
    )
    return fig


def _svg_points(
    df: pd.DataFrame,
    metric: str,
    x_max: float,
    y_min: float,
    y_max: float,
    plot_x: int,
    plot_y: int,
    plot_w: int,
    plot_h: int,
) -> str:
    points = []
    y_span = max(y_max - y_min, 0.001)
    for _, row in df.sort_values("t_min").iterrows():
        value = row.get(metric)
        if pd.isna(value):
            continue
        x = plot_x + (float(row["t_min"]) / max(x_max, 1.0)) * plot_w
        y = plot_y + ((y_max - float(value)) / y_span) * plot_h
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def render_interactive_timeline(long_df: pd.DataFrame, metric: str) -> None:
    """Render an SVG timeline with hover/click trace focusing."""
    if long_df.empty or metric not in long_df.columns:
        st.info("No timeline data available for the selected metric.")
        return

    values = pd.to_numeric(long_df[metric], errors="coerce").dropna()
    if values.empty:
        st.info("No numeric timeline values available for the selected metric.")
        return

    width = 1120
    height = 560
    plot_x = 76
    plot_y = 42
    plot_w = 1006
    plot_h = 356
    x_max = max(float(long_df["t_min"].max()), 1.0)
    y_min = max(0.0, float(values.min()) - 0.04)
    y_max = min(1.0, float(values.max()) + 0.04)
    if y_max - y_min < 0.12:
        y_max = min(1.0, y_min + 0.12)

    series = []
    for idx, (name, group) in enumerate(long_df.groupby("display_label", sort=False)):
        points = _svg_points(group, metric, x_max, y_min, y_max, plot_x, plot_y, plot_w, plot_h)
        if not points:
            continue
        series.append(
            {
                "idx": idx,
                "name": str(name),
                "color": PLOT_COLORS[idx % len(PLOT_COLORS)],
                "points": points,
            }
        )

    if not series:
        st.info("No line series available for the selected sets.")
        return

    x_ticks = [0, 15, 30, 45, 60, 75, 90, 105, 120]
    x_ticks = [tick for tick in x_ticks if tick <= x_max + 1]
    if not x_ticks or x_ticks[-1] < x_max - 5:
        x_ticks.append(round(x_max))

    y_ticks = [y_min + (y_max - y_min) * i / 4 for i in range(5)]

    x_grid = []
    for tick in x_ticks:
        x = plot_x + (tick / max(x_max, 1.0)) * plot_w
        x_grid.append(
            f"""
<line x1="{x:.1f}" y1="{plot_y}" x2="{x:.1f}" y2="{plot_y + plot_h}" class="grid-line x-grid" />
<text x="{x:.1f}" y="{plot_y + plot_h + 34}" class="axis-text" text-anchor="middle">{tick:g}</text>
"""
        )

    y_grid = []
    for tick in y_ticks:
        y = plot_y + ((y_max - tick) / max(y_max - y_min, 0.001)) * plot_h
        y_grid.append(
            f"""
<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x + plot_w}" y2="{y:.1f}" class="grid-line y-grid" />
<text x="{plot_x - 16}" y="{y + 5:.1f}" class="axis-text" text-anchor="end">{tick:.2f}</text>
"""
        )

    line_markup = []
    hit_markup = []
    legend_markup = []
    for item in series:
        safe_name = html.escape(item["name"])
        line_markup.append(
            f"""
<polyline class="signal-line" data-idx="{item['idx']}" data-name="{safe_name}" data-color="{item['color']}"
  points="{item['points']}" fill="none" stroke="{item['color']}" stroke-width="3.8"
  stroke-linecap="round" stroke-linejoin="round" opacity="0.96" />
"""
        )
        hit_markup.append(
            f"""
<polyline class="hit-line" data-idx="{item['idx']}" data-name="{safe_name}"
  points="{item['points']}" fill="none" stroke="transparent" stroke-width="18"
  stroke-linecap="round" stroke-linejoin="round" />
"""
        )
        legend_markup.append(
            f"""
<button class="legend-item" data-idx="{item['idx']}" style="--series-color: {item['color']}">
  <span class="legend-swatch"></span><span>{safe_name}</span>
</button>
"""
        )

    series_json = json.dumps({str(item["idx"]): item["name"] for item in series})
    chart_html = f"""
<div class="timeline-component">
  <div class="timeline-topline">
    <div>
      <div class="timeline-kicker">Interactive signal focus</div>
      <div class="focus-status">Hover a line to isolate it. Click a line or legend item to pin. Click reset to restore.</div>
    </div>
    <button class="reset-focus" type="button">Reset focus</button>
  </div>
  <svg class="timeline-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(metric)} timeline chart">
    <rect x="0" y="0" width="{width}" height="{height}" rx="0" class="svg-panel" />
    <rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" class="plot-panel chart-hit-area" />
    {''.join(x_grid)}
    {''.join(y_grid)}
    <text x="{plot_x + plot_w / 2:.1f}" y="{plot_y + plot_h + 76}" class="axis-label" text-anchor="middle">Time (minutes)</text>
    <text x="22" y="{plot_y + plot_h / 2:.1f}" class="axis-label" transform="rotate(-90 22 {plot_y + plot_h / 2:.1f})" text-anchor="middle">{html.escape(metric)}</text>
    <g class="visible-lines">{''.join(line_markup)}</g>
    <g class="hit-lines">{''.join(hit_markup)}</g>
  </svg>
  <div class="timeline-legend">{''.join(legend_markup)}</div>
</div>

<script>
(() => {{
  const root = document.currentScript.previousElementSibling;
  const names = {series_json};
  let pinned = null;
  const lines = Array.from(root.querySelectorAll('.signal-line'));
  const hits = Array.from(root.querySelectorAll('.hit-line'));
  const legends = Array.from(root.querySelectorAll('.legend-item'));
  const status = root.querySelector('.focus-status');
  const visibleGroup = root.querySelector('.visible-lines');
  const hitGroup = root.querySelector('.hit-lines');

  function setStatus(idx, pinnedState) {{
    if (idx === null || idx === undefined) {{
      status.textContent = 'Hover a line to isolate it. Click a line or legend item to pin. Click reset to restore.';
      return;
    }}
    status.textContent = `${{pinnedState ? 'Pinned' : 'Focused'}}: ${{names[String(idx)]}}`;
  }}

  function resetFocus() {{
    pinned = null;
    lines.forEach((line) => {{
      line.setAttribute('stroke', line.dataset.color);
      line.setAttribute('stroke-width', '3.8');
      line.setAttribute('opacity', '0.96');
      line.classList.remove('is-active', 'is-muted');
    }});
    legends.forEach((legend) => legend.classList.remove('is-active', 'is-muted'));
    setStatus(null, false);
  }}

  function focusLine(idx, pin = false) {{
    const next = String(idx);
    if (pin && pinned === next) {{
      resetFocus();
      return;
    }}
    if (pin) pinned = next;
    const active = pinned || next;
    lines.forEach((line) => {{
      const isActive = line.dataset.idx === active;
      line.setAttribute('stroke', isActive ? line.dataset.color : '#AAB5AF');
      line.setAttribute('stroke-width', isActive ? '6.4' : '2.4');
      line.setAttribute('opacity', isActive ? '1' : '0.24');
      line.classList.toggle('is-active', isActive);
      line.classList.toggle('is-muted', !isActive);
      if (isActive) visibleGroup.appendChild(line);
    }});
    hits.forEach((hit) => {{
      if (hit.dataset.idx === active) hitGroup.appendChild(hit);
    }});
    legends.forEach((legend) => {{
      const isActive = legend.dataset.idx === active;
      legend.classList.toggle('is-active', isActive);
      legend.classList.toggle('is-muted', !isActive);
    }});
    setStatus(active, pinned !== null);
  }}

  hits.forEach((hit) => {{
    hit.addEventListener('mouseenter', () => focusLine(hit.dataset.idx, false));
    hit.addEventListener('mouseleave', () => {{
      if (pinned === null) resetFocus();
    }});
    hit.addEventListener('click', (event) => {{
      event.stopPropagation();
      focusLine(hit.dataset.idx, true);
    }});
  }});

  legends.forEach((legend) => {{
    legend.addEventListener('mouseenter', () => focusLine(legend.dataset.idx, false));
    legend.addEventListener('mouseleave', () => {{
      if (pinned === null) resetFocus();
    }});
    legend.addEventListener('click', (event) => {{
      event.stopPropagation();
      focusLine(legend.dataset.idx, true);
    }});
  }});

  root.querySelector('.reset-focus').addEventListener('click', resetFocus);
  root.querySelector('.chart-hit-area').addEventListener('click', resetFocus);
  resetFocus();
}})();
</script>

<style>
.timeline-component {{
  width: 100%;
  color: #151A1C;
  font-family: Aptos, system-ui, sans-serif;
}}
.timeline-topline {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0 0 0.75rem;
}}
.timeline-kicker {{
  color: #006B4F;
  font-family: "Aptos Mono", monospace;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}}
.focus-status {{
  color: #39413F;
  font-size: 0.94rem;
  margin-top: 0.25rem;
}}
.reset-focus {{
  border: 1px solid #8F9C95;
  color: #151A1C;
  background: #ffffff;
  border-radius: 0;
  padding: 0.55rem 0.9rem;
  font-family: "Aptos Mono", monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  cursor: pointer;
}}
.reset-focus:hover {{
  background: #E7EEE9;
  border-color: #006B4F;
}}
.timeline-svg {{
  display: block;
  width: 100%;
  height: auto;
  filter: none;
}}
.svg-panel {{
  fill: #ffffff;
}}
.plot-panel {{
  fill: #ffffff;
  stroke: #B8C3BC;
  stroke-width: 1.2;
}}
.grid-line {{
  stroke-width: 1;
}}
.x-grid {{
  stroke: #D0D8D2;
}}
.y-grid {{
  stroke: #DEE5E0;
}}
.axis-text, .axis-label {{
  fill: #3A4340;
  font-family: "Aptos Mono", monospace;
  font-size: 16px;
  font-weight: 800;
}}
.axis-label {{
  fill: #151A1C;
  font-size: 19px;
}}
.signal-line {{
  transition: opacity 130ms ease, stroke 130ms ease, stroke-width 130ms ease;
  filter: none;
}}
.hit-line {{
  cursor: pointer;
  pointer-events: stroke;
}}
.timeline-legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.65rem;
}}
.legend-item {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid #AEBAB3;
  border-radius: 0;
  background: #ffffff;
  color: #151A1C;
  padding: 0.42rem 0.68rem;
  font-size: 0.84rem;
  font-weight: 650;
  cursor: pointer;
  transition: opacity 130ms ease, border-color 130ms ease, background 130ms ease;
}}
.legend-swatch {{
  width: 1.7rem;
  height: 0.22rem;
  border-radius: 0;
  background: var(--series-color);
  box-shadow: none;
}}
.legend-item.is-active {{
  border-color: var(--series-color);
  background: #E6F0EA;
}}
.legend-item.is-muted {{
  opacity: 0.36;
}}
</style>
"""
    components.html(chart_html, height=660, scrolling=False)


st.set_page_config(page_title="Boiler Room Crowd Analytics", layout="wide")
inject_theme_css()
render_topbar()
render_hero()

summary_exists = SET_SUMMARY_PATH.exists()
trends_exists = TRENDING_DJ_PATH.exists()

if not summary_exists:
    st.warning("No analysis results yet. Run: python3 run_pipeline.py run --sets-csv data/input/sets.csv")
    st.stop()

summary_df = pd.read_csv(SET_SUMMARY_PATH)
if summary_df.empty:
    st.warning("Summary file is empty. Check your pipeline run.")
    st.stop()

summary_df["display_label"] = summary_df.apply(
    lambda r: f"{r['dj_name']} - {r['set_title']}", axis=1
)
summary_df["chart_label"] = summary_df["dj_name"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

top_avg = summary_df.sort_values("avg_energy", ascending=False).iloc[0]
top_peak = summary_df.sort_values("max_energy", ascending=False).iloc[0]
render_stat_grid(
    [
        ("Best vibes", str(top_avg["dj_name"]), f"avg_energy {float(top_avg['avg_energy']):.3f}"),
        ("Peak reaction", str(top_peak["dj_name"]), f"max_energy {float(top_peak['max_energy']):.3f}"),
        ("Sets analyzed", str(len(summary_df)), "10-second video scoring cadence"),
        ("Track rows", str(count_track_rows()), "Mapped from metadata, fingerprints, and overrides"),
    ]
)

render_section("Analysis decoder")
render_decoder_cards()

if trends_exists:
    render_section("Trending DJs // Top Funnel")
    trends_df = pd.read_csv(TRENDING_DJ_PATH)
    render_dark_table(
        trends_df[[
            "rank",
            "dj_name",
            "trending_score",
            "youtube_hits",
            "youtube_total_views",
            "reddit_posts",
            "reddit_engagement",
        ]],
        max_rows=20,
    )

render_section("Ask CrowdPulse")
st.caption(
    "Ask natural-language questions over the processed CSV outputs. This is the same "
    "logic Codex can run from `python3 run_pipeline.py ask ...`."
)
example_questions = [
    "Which DJ had highest crowd energy?",
    "What are the top songs across sets?",
    "What is the track identification coverage?",
    "Show peak moments for Kaytranada",
]
selected_example = st.selectbox("Example question", example_questions)
custom_question = st.text_input("Question", value=selected_example)
if custom_question.strip():
    st.code(answer_question(custom_question.strip(), top_n=10), language="text")

render_section("Set Comparison")
metric_candidates = [
    "avg_energy",
    "max_energy",
    "high_moment_count",
    "low_moment_count",
    "avg_movement",
    "avg_phone_proxy",
    "avg_lighting_flux",
    "avg_motion_change",
    "avg_texture_density",
    "avg_face_presence",
]
available_metrics = [m for m in metric_candidates if m in summary_df.columns]
metric = st.selectbox("Choose comparison metric", available_metrics)
max_metric_value = float(pd.to_numeric(summary_df[metric], errors="coerce").max() or 0)

fig_bar = px.bar(
    summary_df.sort_values(metric, ascending=True),
    x=metric,
    y="chart_label",
    orientation="h",
    color=metric,
    text=metric,
    hover_data=["set_id", "set_title", "avg_energy", "max_energy"],
    title=f"Comparison by {metric}",
    labels={"chart_label": "DJ / Set", metric: metric},
    color_continuous_scale=[NEON_MAGENTA, NEON_CYAN, ACID_GREEN],
)
style_plotly(fig_bar, height=520)
fig_bar.update_traces(
    texttemplate="%{text:.3f}",
    textposition="outside",
    marker_line={"color": "#FFFFFF", "width": 1},
)
fig_bar.update_layout(
    showlegend=False,
    coloraxis_showscale=False,
    margin={"l": 165, "r": 86, "t": 70, "b": 54},
)
fig_bar.update_xaxes(range=[0, max_metric_value * 1.18 if max_metric_value > 0 else 1])
st.plotly_chart(fig_bar, use_container_width=True)

render_section("Energy Timeline")
set_options = summary_df["set_id"].tolist()
set_label_lookup = dict(zip(summary_df["set_id"], summary_df["display_label"]))
set_dj_lookup = dict(zip(summary_df["set_id"], summary_df["dj_name"]))
default_timeline_sets = summary_df.sort_values("avg_energy", ascending=False).head(4)["set_id"].tolist()
selected_sets = st.multiselect(
    "Sets to plot over time",
    set_options,
    default=default_timeline_sets,
    format_func=lambda sid: set_label_lookup.get(sid, sid),
)

if selected_sets:
    timeline_frames = []
    for set_id in selected_sets:
        path = SCORES_DIR / f"{set_id}_scores.csv"
        if path.exists():
            df = pd.read_csv(path)
            df["display_label"] = set_dj_lookup.get(set_id, set_id)
            timeline_frames.append(df)

    if timeline_frames:
        long_df = pd.concat(timeline_frames, ignore_index=True)
        long_df["t_min"] = long_df["t_sec"] / 60.0

        metric_help = {
            "crowd_energy_smooth": "Rolling-smoothed crowd energy (main signal used for peak/low detection).",
            "crowd_energy": "Composite engagement score from movement, phone activity, lighting changes, motion change, texture, and face presence.",
            "crowd_energy_v1": "Older baseline energy score using only movement + phone proxy.",
            "movement_norm": "Normalized optical-flow movement intensity in the crowd region.",
            "phone_proxy_norm": "Normalized estimate of visible phone filming (bright screen-like blobs).",
            "lighting_flux_norm": "Normalized frame-to-frame lighting/strobe change.",
            "motion_change_norm": "Normalized fraction of pixels that changed noticeably between time samples.",
            "texture_density_norm": "Normalized edge-density proxy for crowd visual density/detail.",
            "face_count_norm": "Normalized face-detection count proxy (presence only, not identity).",
        }

        timeline_metric_candidates = [
            "crowd_energy_smooth",
            "crowd_energy",
            "crowd_energy_v1",
            "movement_norm",
            "phone_proxy_norm",
            "lighting_flux_norm",
            "motion_change_norm",
            "texture_density_norm",
            "face_count_norm",
        ]
        timeline_metrics = [m for m in timeline_metric_candidates if m in long_df.columns]
        selected_timeline_metric = st.selectbox("Timeline metric", timeline_metrics)
        st.caption(f"**{selected_timeline_metric}**: {metric_help.get(selected_timeline_metric, 'No description available.')}")

        with st.expander("Metric definitions"):
            for m in timeline_metrics:
                st.write(f"- `{m}`: {metric_help.get(m, 'No description available.')}")

        render_interactive_timeline(long_df, selected_timeline_metric)

render_section("Peak / Low Moments with Track Mapping")
selected_set_for_table = st.selectbox(
    "Select set",
    set_options,
    format_func=lambda sid: set_label_lookup.get(sid, sid),
)
moments_path = PEAKS_DIR / f"{selected_set_for_table}_moments.csv"
if moments_path.exists():
    moments_df = pd.read_csv(moments_path)
    if "track" not in moments_df.columns:
        moments_df["track"] = "Unknown"
    if "track_source" not in moments_df.columns:
        moments_df["track_source"] = "none"
    if "track_confidence" not in moments_df.columns:
        moments_df["track_confidence"] = 0.0
    high_count = int((moments_df.get("moment_type", "") == "high").sum())
    low_count = int((moments_df.get("moment_type", "") == "low").sum())
    selected_label = set_label_lookup.get(selected_set_for_table, selected_set_for_table)
    st.caption(
        f"{high_count} high moments and {low_count} low moments mapped for "
        f"**{selected_label}**."
    )
    with st.expander(f"Reveal peak / low moment table for {selected_label}", expanded=False):
        render_dark_table(
            moments_df[["t_sec", "moment_type", "crowd_energy_smooth", "track", "track_source", "track_confidence"]]
            .sort_values("t_sec")
            .reset_index(drop=True)
        )
else:
    st.info("No moments file for selected set yet.")

render_section("Top Songs Across Sets")
sets_for_song_rank = selected_sets if selected_sets else set_options
song_frames = []
for set_id in sets_for_song_rank:
    p = PEAKS_DIR / f"{set_id}_moments.csv"
    if not p.exists():
        continue
    df = pd.read_csv(p)
    if df.empty or "track" not in df.columns:
        continue
    df = df.copy()
    df["set_id"] = set_id
    song_frames.append(df)

if not song_frames:
    st.info("No track-mapped moments available yet for selected sets.")
else:
    songs_df = pd.concat(song_frames, ignore_index=True)
    songs_df["track"] = songs_df["track"].fillna("").astype(str).str.strip()
    songs_df = songs_df[~songs_df["track"].isin(["", "Unknown"])]

    if songs_df.empty:
        st.info("No identified tracks found yet in selected sets.")
    else:
        use_high_moments_only = st.checkbox("Use high moments only", value=True)
        if use_high_moments_only and "moment_type" in songs_df.columns:
            songs_df = songs_df[songs_df["moment_type"] == "high"]

        if songs_df.empty:
            st.info("No rows remain after filters.")
        else:
            songs_df["track_key"] = songs_df["track"].apply(canonical_track)
            songs_df["track_confidence"] = pd.to_numeric(
                songs_df.get("track_confidence", 0.0), errors="coerce"
            ).fillna(0.0)

            agg = (
                songs_df.groupby("track_key", dropna=False)
                .agg(
                    track=("track", lambda x: x.value_counts().index[0]),
                    high_moment_hits=("track", "count"),
                    set_coverage=("set_id", "nunique"),
                    avg_energy=("crowd_energy_smooth", "mean"),
                    avg_confidence=("track_confidence", "mean"),
                )
                .reset_index(drop=True)
            )

            rank_mode = st.selectbox(
                "Song ranking",
                [
                    "High-moment hits",
                    "Average crowd energy",
                    "Cross-set coverage",
                ],
            )
            top_n = st.slider("Top songs to show", min_value=5, max_value=30, value=15, step=1)

            if rank_mode == "Average crowd energy":
                ranked = agg.sort_values(
                    ["avg_energy", "high_moment_hits"], ascending=[False, False]
                )
                x_metric = "avg_energy"
            elif rank_mode == "Cross-set coverage":
                ranked = agg.sort_values(
                    ["set_coverage", "high_moment_hits"], ascending=[False, False]
                )
                x_metric = "set_coverage"
            else:
                ranked = agg.sort_values(
                    ["high_moment_hits", "set_coverage"], ascending=[False, False]
                )
                x_metric = "high_moment_hits"

            top_ranked = ranked.head(top_n).copy()

            fig_top_songs = px.bar(
                top_ranked.sort_values(x_metric, ascending=True),
                x=x_metric,
                y="track",
                orientation="h",
                title=f"Top Songs Across Selected Sets ({rank_mode})",
                hover_data=["set_coverage", "avg_energy", "avg_confidence", "high_moment_hits"],
                color=x_metric,
                color_continuous_scale=[NEON_MAGENTA, NEON_CYAN, ACID_GREEN],
            )
            style_plotly(fig_top_songs, height=560)
            fig_top_songs.update_layout(coloraxis_colorbar={"tickfont": {"color": MUTED}, "title": {"font": {"color": INK}}})
            st.plotly_chart(fig_top_songs, use_container_width=True)

            render_dark_table(
                top_ranked[
                    ["track", "high_moment_hits", "set_coverage", "avg_energy", "avg_confidence"]
                ].reset_index(drop=True)
            )

st.caption("Scoring interval is currently 10 seconds by default.")
