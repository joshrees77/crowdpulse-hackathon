# CrowdPulse: Quantifying Emotion Beyond Text

LLMs are becoming extraordinarily good at text: coding, reasoning, summarizing, and operating software all happen in language. But a huge part of being human is not text at all. It is sensory, embodied, and collective: the way a crowd moves when a drop lands, the phones that come out during a peak moment, the energy shift when a song connects, and the shared emotion that appears in video before anyone writes a review.

CrowdPulse is a Codex-built hackathon project exploring a broader vision: creating a structured dataset of human emotional response from real-world sensory media. The MVP uses Boiler Room DJ sets as a testbed because they are long-form, social, musical, and visually rich. It scores crowd energy every 10 seconds, compares DJs and sets, and maps the highest and lowest crowd-reaction moments back to the songs playing at the time.

The long-term idea is bigger than DJ benchmarking. If we can turn video, audio, movement, light, and group behavior into reliable emotional signals, we can build datasets that help digital intelligence understand more of the human experience: concerts, sports, events, classrooms, retail, public spaces, and any moment where emotion is expressed through bodies rather than words.

## Codex Hackathon Angle

This project was built and operated with Codex as the core development partner:
- Codex generated the analysis pipeline, Streamlit dashboard, project docs, demo frame, and PowerPoint pitch deck.
- Natural-language ops let me ask questions like "which set has the best vibes?" or "what are the top songs across sets?" over local analysis outputs.
- A project-specific CrowdPulse skill documents repeatable workflows for refreshing sets, rebuilding tracks, checking demo readiness, and creating artifacts.
- Codex automation/cron workflows can regularly discover new DJ sets, download them, run analysis, and summarize output coverage.
- Codex handled the GitHub packaging flow, including `.gitignore`, commit, and publishing the public repo.

## What It Does

CrowdPulse can:
- discover trending DJs from YouTube and Reddit signals
- download YouTube DJ sets
- score crowd energy every 10 seconds from video
- map peak/low moments to likely tracks from chapters, descriptions, fingerprints, and overrides
- compare sets, DJs, tracks, and moments in a Streamlit dashboard

Current crowd signals:
- movement intensity (optical flow)
- phone-filming proxy (bright screen-like blobs)
- lighting flux / strobe dynamics
- motion-change ratio
- crowd texture density proxy
- optional face-presence proxy (face detection only, no identity recognition)

Current track identification stack:
- YouTube chapters from info JSON (`source=youtube_chapter`, high confidence)
- Timestamp lines in video description (`source=description_timestamp`, medium confidence)
- Audio fingerprint fallback from sampled set audio (`source=audio_fingerprint`, medium-high confidence)
- Manual corrections from `data/input/manual_track_overrides.csv` (`source=manual_override`, highest confidence)

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requirements:
- `ffmpeg` installed and available in `PATH`
- `yt-dlp` installed and available in `PATH`

## 2) Add your sets

Edit:
- `data/input/sets.csv`

Required columns:
- `set_id`
- `dj_name`
- `set_title`
- `youtube_url`

## 3) Run trend discovery only

```bash
python3 run_pipeline.py discover
```

Output:
- `data/processed/trends/trending_djs.csv`

## 4) Build a top-10 set list from trends

```bash
python3 run_pipeline.py prepare-top10 --top-n 10 --output data/input/sets.csv
```

## 5) Download only (no analysis yet)

```bash
python3 run_pipeline.py download --sets-csv data/input/sets.csv
```

## 6) Run full pipeline

```bash
python3 run_pipeline.py run --sets-csv data/input/sets.csv --interval 10
```

## 6b) One-command recurring refresh flow

```bash
python3 run_pipeline.py refresh-top10 --top-n 10 --sets-csv data/input/sets.csv --interval 10
```

This command does:
1. Discover trends (YouTube + Reddit)
2. Rebuild top set list
3. Download new sets
4. Run analysis and track mapping

## 6c) Rebuild only track timelines

```bash
python3 run_pipeline.py refresh-tracks --sets-csv data/input/sets.csv
```

Use this when video scoring is already done and you only want better track mapping.

Equivalent helper script:

```bash
./scripts/refresh_top10.sh
```

## 6d) Ask questions and self-check the run

Natural-language analytics over the processed CSV outputs:

```bash
python3 run_pipeline.py ask "Which DJ had highest crowd energy?"
python3 run_pipeline.py ask "What are the top songs across sets?" --top-n 5
python3 run_pipeline.py ask "What is the track identification coverage?"
```

Self-healing / pre-demo diagnostic check:

```bash
python3 run_pipeline.py doctor
```

Demo artifact generation:

```bash
python3 scripts/export_demo_frame.py --set-id set_1_unknown_dj --t-sec 2830
```

Project-specific Codex workflow:

```text
.agents/skills/crowdpulse/SKILL.md
```

This skill documents the repeatable Codex operating loop: refresh the top sets, answer questions, rebuild track mappings, run the doctor check, generate demo frames, and update the pitch deck.

Outputs:
- downloaded videos: `data/raw/videos/`
- metadata JSON: `data/raw/meta/`
- time-series scores: `data/processed/scores/*_scores.csv`
- peak/low moments: `data/processed/peaks/*_moments.csv`
- tracklist parses: `data/processed/tracks/*_tracks.csv`
- cross-set summary: `data/processed/set_summary.csv`

Optional manual track override file:
- `data/input/manual_track_overrides.csv`

Suggested columns:
- `set_id,start_sec,track`
- or `set_id,timestamp,track` (timestamp like `01:23:40`)

Moment output includes:
- `track`
- `track_source`
- `track_confidence`

## 7) Run regularly

For a local cron job (daily at 9:00 AM):

```bash
0 9 * * * cd /Users/joshrees/Desktop/CODEX\\ hackathib && ./scripts/refresh_top10.sh >> data/processed/cron_refresh.log 2>&1
```

The Codex desktop automation for this project runs the same refresh script, then uses `doctor` to summarize output coverage.

## 8) Launch dashboard

```bash
streamlit run app.py
```

Dashboard views:
- trending DJ table
- Ask CrowdPulse natural-language Q&A
- set comparison bar chart
- crowd energy timeline comparison
- timeline metric selector (movement, phone proxy, lighting flux, face presence, etc.)
- peak/low moments with mapped track names
- top songs across selected sets

## Notes on model quality

This MVP uses fast, heuristic computer vision (optical flow + bright-screen proxy). It is built for hackathon demos, not production-grade behavioral inference.

Recommended quick upgrades after hackathon:
1. Replace phone proxy with object detection model (person + phone classes)
2. Add beat/drop-aware audio features
3. Add manual review UI for correcting track mappings
4. Add camera-motion compensation for more stable movement scoring
