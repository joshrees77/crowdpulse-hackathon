# CrowdPulse

### Quantifying human emotion beyond text

AI is getting very good at understanding what people say. CrowdPulse explores how AI might understand what people feel.

This Codex hackathon project turns Boiler Room DJ sets into a structured signal of crowd emotion. It downloads long-form set videos, scores audience energy every 10 seconds, compares DJs and sets, and maps the highest and lowest crowd reactions back to the tracks playing at that moment.

The bigger vision is a dataset of human emotional response from sensory media: movement, light, sound, phones, faces, and group behavior. Boiler Room is the prototype, but the same idea could apply to concerts, sports, classrooms, retail, brand activations, and any real-world experience where emotion is expressed through bodies rather than words.

## What It Proves

CrowdPulse is a working MVP for emotion intelligence beyond language:

- **Crowd reaction as data:** video is converted into 10-second crowd-energy timelines.
- **Benchmarkable experiences:** DJs, sets, tracks, and moments can be compared with the same scoring pipeline.
- **Songs linked to emotion:** peak and low crowd moments are mapped to likely tracks using chapters, descriptions, fingerprints, and manual overrides.
- **Human-readable analysis:** a Streamlit dashboard turns the outputs into rankings, timelines, moment tables, and natural-language Q&A.
- **Repeatable pipeline:** new sets can be discovered, downloaded, scored, checked, and summarized with one command.

## How Codex Was Used

Codex was not just autocomplete for this project. It acted like a product engineer, data operator, designer, and launch assistant:

- Built the Python analysis pipeline, Streamlit dashboard, track-mapping workflow, and diagnostics.
- Added natural-language analytics so I can ask questions like `which set has the best vibes?` or `what are the top songs across sets?`.
- Created a project-specific CrowdPulse skill for repeatable operations: refresh sets, rebuild tracks, run checks, generate demo frames, and update the pitch deck.
- Set up automation/cron workflows to regularly discover new sets and rerun analysis.
- Generated the annotated demo frame, hackathon blurb, PowerPoint pitch deck, README, `.gitignore`, commits, and public GitHub repo.

## How It Works

1. **Discover:** rank trending DJs using YouTube and Reddit signals.
2. **Ingest:** download set metadata and YouTube videos with `yt-dlp`.
3. **Score:** sample frames every 10 seconds and compute crowd-reaction proxies.
4. **Map:** align high/low reaction moments with track timelines.
5. **Explore:** compare sets in the dashboard or ask questions over the processed CSVs.

### Crowd Signals

- movement intensity from optical flow
- phone-filming proxy from bright screen-like regions
- lighting flux and strobe dynamics
- motion-change ratio
- crowd texture density proxy
- optional face-presence proxy, with no identity recognition

### Track Identification

- YouTube chapters, highest confidence
- timestamped video descriptions
- sampled audio fingerprint fallback
- manual corrections in `data/input/manual_track_overrides.csv`

## Demo Artifacts

- Dashboard: `app.py`
- Pitch deck: `outputs/boiler-room-pitch/CrowdPulse_Hackathon_Pitch.pptx`
- Demo frame: `data/processed/demo_frames/set_1_unknown_dj_2830s_annotated.jpg`
- Summary data: `data/processed/set_summary.csv`
- Score timelines: `data/processed/scores/*_scores.csv`
- Peak/low moments: `data/processed/peaks/*_moments.csv`
- Track timelines: `data/processed/tracks/*_tracks.csv`

Raw videos are intentionally excluded from GitHub because they are large and can be recreated from the set manifests.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requirements:

- `ffmpeg`
- `yt-dlp`

Run the dashboard:

```bash
streamlit run app.py
```

Run the full refresh pipeline:

```bash
python3 run_pipeline.py refresh-top10 --top-n 10 --sets-csv data/input/sets.csv --interval 10
```

Ask the processed data questions:

```bash
python3 run_pipeline.py ask "Which DJ had highest crowd energy?"
python3 run_pipeline.py ask "What are the top songs across sets?" --top-n 5
python3 run_pipeline.py ask "What is the track identification coverage?"
```

Check demo readiness:

```bash
python3 run_pipeline.py doctor
```

Generate an annotated frame:

```bash
python3 scripts/export_demo_frame.py --set-id set_1_unknown_dj --t-sec 2830
```

## Project Structure

```text
boilerroom_tool/        analysis, ingest, track mapping, Q&A, diagnostics
app.py                  Streamlit dashboard
data/input/             set lists and manual track overrides
data/processed/         committed demo outputs and analysis CSVs
outputs/                hackathon pitch deck
scripts/                helper scripts
.agents/skills/         CrowdPulse Codex skill
```

## Next Steps

- Replace heuristic phone detection with object detection for people and phones.
- Add beat/drop-aware audio features.
- Improve camera-motion compensation for handheld or moving shots.
- Build a review UI for correcting track mappings and labeling emotional moments.
- Scale from DJ sets to a broader emotional-response dataset across live experiences.

## Caveat

This is a hackathon MVP. The current scores are fast computer-vision proxies for crowd reaction, not a production-grade measure of internal emotion. The point is to prove the loop: sensory media can be converted into structured emotional-response data that humans and AI systems can query, compare, and improve.
