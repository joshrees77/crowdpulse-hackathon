---
name: crowdpulse
description: Use this skill when working on the CrowdPulse Boiler Room crowd-reaction analyzer, including refreshing trending DJ sets, downloading YouTube sets, rerunning crowd analysis, rebuilding track identification, answering natural-language analytics questions, creating demo frames, or updating the hackathon pitch deck.
metadata:
  short-description: Operate the CrowdPulse crowd-reaction analyzer
---

# CrowdPulse

CrowdPulse is a local pipeline and Streamlit dashboard for analyzing crowd reaction in DJ sets.

## Core Commands

Run commands from the project root:

```bash
cd /Users/joshrees/Desktop/CODEX\ hackathib
source .venv/bin/activate
```

Refresh discovery, downloads, analysis, and track mapping:

```bash
python3 run_pipeline.py refresh-top10 --top-n 10 --sets-csv data/input/sets.csv --interval 10
```

Answer analytics questions from processed CSV outputs:

```bash
python3 run_pipeline.py ask "Which DJ had the highest crowd energy?"
python3 run_pipeline.py ask "What are the top songs across sets?"
python3 run_pipeline.py ask "Compare Kaytranada and Fred again"
```

Rebuild track mappings only:

```bash
python3 run_pipeline.py refresh-tracks --sets-csv data/input/sets.csv
```

Check local health and data coverage:

```bash
python3 run_pipeline.py doctor
```

Generate an annotated demo frame:

```bash
python3 scripts/export_demo_frame.py --set-id set_1_unknown_dj --t-sec 2830
```

Launch the dashboard:

```bash
streamlit run app.py --server.port 8501
```

## Output Files

- `data/processed/set_summary.csv`: set-level metrics and rankings
- `data/processed/scores/*_scores.csv`: 10-second metric timelines
- `data/processed/peaks/*_moments.csv`: high/low moments with mapped tracks
- `data/processed/tracks/*_tracks.csv`: track timelines and sources
- `data/processed/download_manifest.csv`: downloaded video labels and file paths
- `outputs/boiler-room-pitch/CrowdPulse_Hackathon_Pitch.pptx`: pitch deck

## Operating Guidance

- Prefer `refresh-top10` for a complete scheduled run.
- Prefer `ask` for fast natural-language summaries without rerunning analysis.
- Prefer `refresh-tracks` when song mapping changes but crowd scoring is already done.
- Prefer `doctor` before demos to confirm dependencies and output coverage.
