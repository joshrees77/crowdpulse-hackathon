# Boiler Room Crowd Reaction Analyzer (Hackathon Blurb)

## What this app does
This app automatically finds trending DJs, downloads their YouTube Boiler Room sets, and scores crowd reaction over time so we can compare DJ/set performance and identify which songs drive the strongest audience response.

## End-to-end workflow
1. **Top of funnel (discovery):** The pipeline ranks trending DJs using a blended score from YouTube set visibility and Reddit mention/engagement signals.
2. **Set ingestion:** The top sets are downloaded from YouTube and saved with metadata (title, uploader, description, etc.).
3. **Crowd analysis (every 10s):** For each set, the app samples video frames and computes audience-engagement proxies:
   - movement intensity (optical flow)
   - phone-filming proxy (bright screen-like detections)
   - lighting flux (strobe/brightness change)
   - motion change ratio
   - texture density proxy
   - face presence proxy (detection only, no identity recognition)
4. **Scoring:** These normalized signals are combined into `crowd_energy`, then smoothed into `crowd_energy_smooth` for robust peak/low detection.
5. **Track identification:** The app maps peak/low moments to songs using a fallback stack:
   - YouTube chapters (if present)
   - timestamped tracklists from descriptions
   - audio fingerprint recognition from sampled clips
   - optional manual overrides for corrections
6. **Comparison dashboard:** Streamlit visualizes DJ/set comparisons, engagement timelines, peak/low moment tables, and top songs across sets.

## What you can learn from it
- Which DJs consistently produce stronger crowd energy
- Where each set peaks/dips across time
- Which tracks are most associated with high-energy moments
- Cross-set song performance patterns for programming and A&R-style decisions

## Why this works for a hackathon
- Fully local, laptop-friendly workflow
- Fast heuristic vision metrics with meaningful signal for demo purposes
- Modular pipeline that can be upgraded with stronger models/APIs post-hackathon
- Supports recurring refresh runs for continuously updated rankings and analysis

## Codex-powered operating loop
- **Project skill:** `.agents/skills/crowdpulse/SKILL.md` packages the repeatable commands for refreshes, diagnostics, Q&A, demo-frame generation, and deck updates.
- **Natural-language analytics:** `python3 run_pipeline.py ask "What are the top songs across sets?"` answers questions from the processed CSV outputs.
- **Diagnostics:** `python3 run_pipeline.py doctor` checks dependencies and output coverage before a demo.
- **Recurring analysis:** `./scripts/refresh_top10.sh` runs discovery, downloads, scoring, and track mapping as a single scheduled workflow.
- **Artifacts:** Codex generated the annotated example frame, dashboard updates, documentation, and editable PowerPoint pitch deck from the same local project outputs.
