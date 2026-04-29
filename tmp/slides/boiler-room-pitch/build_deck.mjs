// Node-oriented editable pro deck builder.
// Run this after editing SLIDES, SOURCES, and layout functions.
// The init script installs a sibling node_modules/@oai/artifact-tool package link
// and package.json with type=module for shell-run eval builders. Run with the
// Node executable from Codex workspace dependencies or the platform-appropriate
// command emitted by the init script.
// Do not use pnpm exec from the repo root or any Node binary whose module
// lookup cannot resolve the builder's sibling node_modules/@oai/artifact-tool.

const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;

const DECK_ID = "boiler-room-pitch";
const OUT_DIR = "/Users/joshrees/Desktop/CODEX hackathib/outputs/boiler-room-pitch";
const REF_DIR = "/Users/joshrees/Desktop/CODEX hackathib/tmp/slides/boiler-room-pitch/pro-reference-images";
const SCRATCH_DIR = path.resolve(process.env.PPTX_SCRATCH_DIR || path.join("tmp", "slides", DECK_ID));
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const VERIFICATION_DIR = path.join(SCRATCH_DIR, "verification");
const INSPECT_PATH = path.join(SCRATCH_DIR, "inspect.ndjson");
const MAX_RENDER_VERIFY_LOOPS = 3;

const INK = "#151A1C";
const GRAPHITE = "#2E3734";
const MUTED = "#4D5654";
const PAPER = "#F7F8F5";
const PAPER_96 = "#FFFFFF";
const WHITE = "#FFFFFF";
const ACCENT = "#006B4F";
const ACCENT_DARK = "#006B4F";
const GOLD = "#A06A00";
const CORAL = "#C2415D";
const MAGENTA = "#B01875";
const VIOLET = "#6E3FA3";
const ACID = "#258A45";
const BLUE = "#1F75B6";
const BORDER_SOFT = "#C9D2CC";
const BORDER_STRONG = "#8F9C95";
const PANEL_LINE = BORDER_STRONG;
const PANEL_SHADOW = "#C9D2CC66";
const PANEL_TINT = "#F1F4EF";
const TRANSPARENT = "#00000000";

const TITLE_FACE = "Aptos Display";
const BODY_FACE = "Aptos";
const MONO_FACE = "Aptos Mono";

const FALLBACK_PLATE_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

const SOURCES = {
  primary: "Local run outputs from Boiler Room Crowd Reaction Analyzer.",
  summary: "data/processed/set_summary.csv (top-10 set analysis).",
  leaderboard: "data/processed/leaderboard_top10.csv (ranking by avg_energy).",
  tracks: "data/processed/tracks/*_tracks.csv (audio-fingerprint track mapping).",
  moments: "data/processed/peaks/*_moments.csv (high/low crowd moments).",
};

const SLIDES = [
  {
    "kicker": "HACKATHON PITCH",
    "title": "CrowdPulse: Quantifying Emotion Beyond Text",
    "subtitle": "LLMs excel in text and code. We add a sensory layer that measures crowd emotion from video over time.",
    "expectedVisual": "Title slide with clear product framing and immediate value proposition.",
    "moment": "From text intelligence to emotion intelligence",
    "notes": "Open with your thesis: if AI should understand humans, it must model emotional experience beyond text.",
    "sources": [
      "primary",
      "summary"
    ]
  },
  {
    "kicker": "PROBLEM",
    "title": "Text-native intelligence misses sensory emotional context",
    "subtitle": "Human emotional experience is not only text; it is movement, sound, light, and collective behavior.",
    "expectedVisual": "Three pain-point cards with practical business impact.",
    "cards": [
      [
        "LLMs are text-first",
        "Most digital workflows are language and code, where LLMs are excellent."
      ],
      [
        "Emotion is sensory",
        "Crowd emotion appears in movement, rhythm, lighting shifts, and group reaction."
      ],
      [
        "Opportunity",
        "Quantify these signals and you unlock measurable emotional intelligence."
      ]
    ],
    "notes": "Bridge from philosophy to product: we operationalize emotional signal in a repeatable pipeline.",
    "sources": [
      "primary"
    ]
  },
  {
    "kicker": "RESULTS",
    "title": "Top-10 benchmark run produced clear DJ performance spread",
    "subtitle": "Same pipeline, same cadence, and normalized signals make cross-set ranking possible.",
    "expectedVisual": "Three metric cards showing strongest benchmark evidence.",
    "metrics": [
      [
        "0.498",
        "Top avg_energy (Kaytranada set)",
        "From leaderboard_top10"
      ],
      [
        "0.286",
        "Lowest avg_energy (Acid Pauli set)",
        "From leaderboard_top10"
      ],
      [
        "10",
        "Sets fully analyzed in local run",
        "From set_summary.csv"
      ]
    ],
    "notes": "Call out that relative spread is the value: we can now compare crowd reaction quantitatively.",
    "sources": [
      "summary",
      "leaderboard"
    ]
  },
  {
    "kicker": "HOW IT WORKS",
    "title": "Automated pipeline from discovery to time-coded insights",
    "subtitle": "The workflow is modular, repeatable, and designed for regular refresh runs.",
    "expectedVisual": "Three cards summarizing ingestion, scoring, and track mapping.",
    "demoFramePath": "/Users/joshrees/Desktop/CODEX hackathib/data/processed/demo_frames/set_1_unknown_dj_2830s_annotated.jpg",
    "cards": [
      [
        "Discover + ingest",
        "Rank trending DJs, then ingest top YouTube sets with metadata."
      ],
      [
        "Score crowd energy",
        "Every 10 seconds we score movement, phones, lighting, and crowd motion."
      ],
      [
        "Map songs to moments",
        "Map high/low moments to tracks using metadata and fingerprinting."
      ]
    ],
    "notes": "Explain that each module can be upgraded independently (better detection models, stronger fingerprint APIs).",
    "sources": [
      "primary",
      "tracks",
      "moments"
    ]
  },
  {
    "kicker": "CODEX FEATURES",
    "title": "Natural-language Ops in Codex",
    "subtitle": "Codex operates the project as a repeatable system: skill, Q&A, automation, diagnostics, and artifacts.",
    "expectedVisual": "Three cards highlighting concrete Codex capabilities used during the hackathon.",
    "cards": [
      [
        "CrowdPulse skill",
        "Skill packages refresh, Q&A, checks, frames, and deck tasks."
      ],
      [
        "Ask the data",
        "run_pipeline.py ask answers DJ, song, track, and peak questions."
      ],
      [
        "Cron + artifacts",
        "Automation refreshes top sets; Codex creates this deck and demo frames."
      ]
    ],
    "notes": "Show NL-to-ops mapping: 'scrape more sets' maps to run_pipeline.py refresh-top10 --top-n 20; 'ask top songs' maps to run_pipeline.py ask; 'check if demo-ready' maps to run_pipeline.py doctor. Mention the installed CrowdPulse skill, PowerPoint skill deck generation, the daily automation named CrowdPulse top-10 DJ refresh, and human review through data/input/manual_track_overrides.csv.",
    "sources": [
      "primary"
    ]
  },
  {
    "kicker": "NEXT PHASE",
    "title": "Roadmap: crowd analytics to emotional intelligence",
    "subtitle": "This MVP is the first step toward quantifying real-world emotional experience at scale.",
    "expectedVisual": "Three metric-style cards for roadmap priorities.",
    "metrics": [
      [
        "1",
        "Add track-ID providers + confidence calibration",
        "Higher song precision"
      ],
      [
        "2",
        "Add person/phone detection + camera-motion compensation",
        "More stable engagement signal"
      ],
      [
        "3",
        "Generalize to sports, concerts, and brand activations",
        "Broader emotional-intelligence platform"
      ]
    ],
    "notes": "Close with ask: pilot with one promoter/label and benchmark 50+ sets in the next cycle.",
    "sources": [
      "primary"
    ]
  }
];

const inspectRecords = [];

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  if (!bytes.byteLength) {
    throw new Error(`Image file is empty: ${imagePath}`);
  }
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function normalizeImageConfig(config) {
  if (!config.path) {
    return config;
  }
  const { path: imagePath, ...rest } = config;
  return {
    ...rest,
    blob: await readImageBlob(imagePath),
  };
}

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const obsoleteFinalArtifacts = [
    "preview",
    "verification",
    "inspect.ndjson",
    ["presentation", "proto.json"].join("_"),
    ["quality", "report.json"].join("_"),
  ];
  for (const obsolete of obsoleteFinalArtifacts) {
    await fs.rm(path.join(OUT_DIR, obsolete), { recursive: true, force: true });
  }
  await fs.mkdir(SCRATCH_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(VERIFICATION_DIR, { recursive: true });
}

function lineConfig(fill = TRANSPARENT, width = 0) {
  return { style: "solid", fill, width };
}

function recordShape(slideNo, shape, role, shapeType, x, y, w, h) {
  if (!slideNo) return;
  inspectRecords.push({
    kind: "shape",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    shapeType,
    bbox: [x, y, w, h],
  });
}

function addShape(slide, geometry, x, y, w, h, fill = TRANSPARENT, line = TRANSPARENT, lineWidth = 0, meta = {}) {
  const shape = slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: lineConfig(line, lineWidth),
  });
  recordShape(meta.slideNo, shape, meta.role || geometry, geometry, x, y, w, h);
  return shape;
}

function seededNoise(seed) {
  const raw = Math.sin(seed * 999.73) * 10000;
  return raw - Math.floor(raw);
}

function addGlitchBackdrop(slide, slideNo, density = "normal") {
  slide.background.fill = PAPER;
  addShape(slide, "rect", 0, 0, W, H, PAPER, TRANSPARENT, 0, { slideNo, role: "clean canvas" });
  addShape(slide, "rect", 0, H - 76, W, 76, "#EFF3F066", TRANSPARENT, 0, { slideNo, role: "soft footer wash" });

  for (let y = 96; y < H - 92; y += 56) {
    addShape(slide, "rect", 0, y, W, 1, "#DDE5E038", TRANSPARENT, 0, { slideNo, role: "subtle gridline" });
  }

  addShape(slide, "rect", 164, 64, 196, 10, "#006B4F18", TRANSPARENT, 0, { slideNo, role: "quiet signal mark" });
  addShape(slide, "rect", 918, 80, 112, 3, "#B0187538", TRANSPARENT, 0, { slideNo, role: "quiet signal mark" });
  if (density === "cover") {
    addShape(slide, "rect", 96, 586, 168, 5, "#006B4F24", TRANSPARENT, 0, { slideNo, role: "cover quiet signal mark" });
    addShape(slide, "rect", 292, 586, 122, 5, "#1F75B620", TRANSPARENT, 0, { slideNo, role: "cover quiet signal mark" });
  }
}

function normalizeText(text) {
  if (Array.isArray(text)) {
    return text.map((item) => String(item ?? "")).join("\n");
  }
  return String(text ?? "");
}

function textLineCount(text) {
  const value = normalizeText(text);
  if (!value.trim()) {
    return 0;
  }
  return Math.max(1, value.split(/\n/).length);
}

function requiredTextHeight(text, fontSize, lineHeight = 1.18, minHeight = 8) {
  const lines = textLineCount(text);
  if (lines === 0) {
    return minHeight;
  }
  return Math.max(minHeight, lines * fontSize * lineHeight);
}

function assertTextFits(text, boxHeight, fontSize, role = "text") {
  const required = requiredTextHeight(text, fontSize);
  const tolerance = Math.max(2, fontSize * 0.08);
  if (normalizeText(text).trim() && boxHeight + tolerance < required) {
    throw new Error(
      `${role} text box is too short: height=${boxHeight.toFixed(1)}, required>=${required.toFixed(1)}, ` +
        `lines=${textLineCount(text)}, fontSize=${fontSize}, text=${JSON.stringify(normalizeText(text).slice(0, 90))}`,
    );
  }
}

function wrapText(text, widthChars) {
  const words = normalizeText(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > widthChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines.join("\n");
}

function recordText(slideNo, shape, role, text, x, y, w, h) {
  const value = normalizeText(text);
  inspectRecords.push({
    kind: "textbox",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    text: value,
    textPreview: value.replace(/\n/g, " | ").slice(0, 180),
    textChars: value.length,
    textLines: textLineCount(value),
    bbox: [x, y, w, h],
  });
}

function recordImage(slideNo, image, role, imagePath, x, y, w, h) {
  inspectRecords.push({
    kind: "image",
    slide: slideNo,
    id: image?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    path: imagePath,
    bbox: [x, y, w, h],
  });
}

function applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle) {
  box.text = text;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = Boolean(bold);
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.typeface = face;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  if (autoFit) {
    box.text.autoFit = autoFit;
  }
  if (listStyle) {
    box.text.style = "list";
  }
}

function addText(
  slide,
  slideNo,
  text,
  x,
  y,
  w,
  h,
  {
    size = 22,
    color = INK,
    bold = false,
    face = BODY_FACE,
    align = "left",
    valign = "top",
    fill = TRANSPARENT,
    line = TRANSPARENT,
    lineWidth = 0,
    autoFit = null,
    listStyle = false,
    checkFit = true,
    role = "text",
  } = {},
) {
  if (!checkFit && textLineCount(text) > 1) {
    throw new Error("checkFit=false is only allowed for single-line headers, footers, and captions.");
  }
  if (checkFit) {
    assertTextFits(text, h, size, role);
  }
  const box = addShape(slide, "rect", x, y, w, h, fill, line, lineWidth);
  applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle);
  recordText(slideNo, box, role, text, x, y, w, h);
  return box;
}

async function addImage(slide, slideNo, config, position, role, sourcePath = null) {
  const image = slide.images.add(await normalizeImageConfig(config));
  image.position = position;
  recordImage(slideNo, image, role, sourcePath || config.path || config.uri || "inline-data-url", position.left, position.top, position.width, position.height);
  return image;
}

async function addPlate(slide, slideNo, opacityPanel = false) {
  addGlitchBackdrop(slide, slideNo, slideNo === 1 ? "cover" : "normal");
  if (opacityPanel) {
    addShape(slide, "rect", 0, 0, W, H, "#FFFFFFB8", TRANSPARENT, 0, { slideNo, role: "plate readability overlay" });
  }
}

function addHeader(slide, slideNo, kicker, idx, total) {
  addShape(slide, "rect", 64, 62, 1152, 1, BORDER_SOFT, TRANSPARENT, 0, { slideNo, role: "header divider" });
  addText(slide, slideNo, String(kicker || "").toUpperCase(), 64, 34, 430, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "header",
  });
  addText(slide, slideNo, `${String(idx).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, 1114, 34, 104, 24, {
    size: 13,
    color: MUTED,
    bold: true,
    face: MONO_FACE,
    align: "right",
    checkFit: false,
    role: "header",
  });
  addShape(slide, "rect", 64, 66, 1152, 2, ACCENT, TRANSPARENT, 0, { slideNo, role: "header rule" });
  addShape(slide, "rect", 57, 57, 16, 16, ACCENT, TRANSPARENT, 0, { slideNo, role: "header marker" });
  addShape(slide, "rect", 82, 58, 52, 4, ACID, TRANSPARENT, 0, { slideNo, role: "header signal chip" });
  addShape(slide, "rect", 1080, 66, 52, 3, MAGENTA, TRANSPARENT, 0, { slideNo, role: "header signal chip" });
}

function addTitleBlock(slide, slideNo, title, subtitle = null, x = 64, y = 86, w = 780, dark = false) {
  const titleColor = INK;
  const bodyColor = GRAPHITE;
  addText(slide, slideNo, title, x - 4, y + 2, w, 142, {
    size: 40,
    color: TRANSPARENT,
    bold: true,
    face: TITLE_FACE,
    role: "title rgb shadow",
  });
  addText(slide, slideNo, title, x + 4, y - 2, w, 142, {
    size: 40,
    color: TRANSPARENT,
    bold: true,
    face: TITLE_FACE,
    role: "title rgb shadow",
  });
  addText(slide, slideNo, title, x, y, w, 142, {
    size: 40,
    color: titleColor,
    bold: true,
    face: TITLE_FACE,
    role: "title",
  });
  if (subtitle) {
    addShape(slide, "rect", x, y + 136, 94, 3, MAGENTA, TRANSPARENT, 0, { slideNo, role: "title glitch underline" });
    addShape(slide, "rect", x + 104, y + 136, 38, 3, ACCENT, TRANSPARENT, 0, { slideNo, role: "title glitch underline" });
    addText(slide, slideNo, subtitle, x + 2, y + 148, Math.min(w, 720), 70, {
      size: 19,
      color: bodyColor,
      face: BODY_FACE,
      role: "subtitle",
    });
  }
}

function addIconBadge(slide, slideNo, x, y, accent = ACCENT, kind = "signal") {
  addShape(slide, "ellipse", x + 3, y + 2, 54, 54, PANEL_SHADOW, TRANSPARENT, 0, { slideNo, role: "icon shadow" });
  addShape(slide, "ellipse", x, y, 54, 54, WHITE, PANEL_LINE, 1.2, { slideNo, role: "icon badge" });
  if (kind === "flow") {
    addShape(slide, "ellipse", x + 13, y + 18, 10, 10, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "ellipse", x + 31, y + 27, 10, 10, ACID, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 22, y + 25, 19, 3, ACCENT, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  } else if (kind === "layers") {
    addShape(slide, "roundRect", x + 13, y + 15, 26, 13, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 18, y + 24, 26, 13, GOLD, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 23, y + 33, 20, 10, CORAL, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  } else {
    addShape(slide, "rect", x + 16, y + 29, 6, 12, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 25, y + 21, 6, 20, ACID, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 34, y + 14, 6, 27, MAGENTA, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  }
}

function addCard(slide, slideNo, x, y, w, h, label, body, { accent = ACCENT, fill = PAPER_96, line = INK, iconKind = "signal" } = {}) {
  if (h < 156) {
    throw new Error(`Card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=156.`);
  }
  addShape(slide, "roundRect", x + 6, y + 6, w, h, PANEL_SHADOW, TRANSPARENT, 0, { slideNo, role: `card shadow: ${label}` });
  addShape(slide, "roundRect", x, y, w, h, fill, PANEL_LINE, 1.1, { slideNo, role: `card panel: ${label}` });
  addShape(slide, "rect", x, y, w, 6, accent, TRANSPARENT, 0, { slideNo, role: `card accent: ${label}` });
  addShape(slide, "rect", x + w - 70, y + 15, 48, 3, MAGENTA, TRANSPARENT, 0, { slideNo, role: `card accent chip: ${label}` });
  addShape(slide, "rect", x + w - 112, y + 15, 28, 3, ACID, TRANSPARENT, 0, { slideNo, role: `card accent chip: ${label}` });
  addIconBadge(slide, slideNo, x + 22, y + 24, accent, iconKind);
  addText(slide, slideNo, label, x + 88, y + 22, w - 108, 28, {
    size: 15,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "card label",
  });
  const wrapped = wrapText(body, Math.max(28, Math.floor(w / 13)));
  const bodyY = y + 86;
  const bodyH = h - (bodyY - y) - 22;
  if (bodyH < 54) {
    throw new Error(`Card body area is too short: height=${bodyH.toFixed(1)}, cardHeight=${h.toFixed(1)}, label=${JSON.stringify(label)}.`);
  }
  addText(slide, slideNo, wrapped, x + 24, bodyY, w - 48, bodyH, {
    size: 17,
    color: GRAPHITE,
    face: BODY_FACE,
    role: `card body: ${label}`,
  });
}

function addMetricCard(slide, slideNo, x, y, w, h, metric, label, note = null, accent = ACCENT) {
  if (h < 132) {
    throw new Error(`Metric card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=132.`);
  }
  addShape(slide, "roundRect", x + 6, y + 6, w, h, PANEL_SHADOW, TRANSPARENT, 0, { slideNo, role: `metric shadow: ${label}` });
  addShape(slide, "roundRect", x, y, w, h, WHITE, PANEL_LINE, 1.1, { slideNo, role: `metric panel: ${label}` });
  addShape(slide, "rect", x, y, w, 7, accent, TRANSPARENT, 0, { slideNo, role: `metric accent: ${label}` });
  addShape(slide, "rect", x + w - 60, y + 18, 32, 4, MAGENTA, TRANSPARENT, 0, { slideNo, role: `metric accent chip: ${label}` });
  addText(slide, slideNo, metric, x + 22, y + 24, w - 44, 54, {
    size: 34,
    color: accent,
    bold: true,
    face: TITLE_FACE,
    role: "metric value",
  });
  addText(slide, slideNo, label, x + 24, y + 82, w - 48, 38, {
    size: 16,
    color: INK,
    face: BODY_FACE,
    role: "metric label",
  });
  if (note) {
    addText(slide, slideNo, note, x + 24, y + h - 42, w - 48, 22, {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      role: "metric note",
    });
  }
}

function addNotes(slide, body, sourceKeys) {
  const sourceLines = (sourceKeys || []).map((key) => `- ${SOURCES[key] || key}`).join("\n");
  slide.speakerNotes.setText(`${body || ""}\n\n[Sources]\n${sourceLines}`);
}

function addReferenceCaption(slide, slideNo) {
  addText(
    slide,
    slideNo,
    "Editable PowerPoint deck: copy, cards, metrics, signal marks, and demo frame.",
    64,
    674,
    980,
    22,
    {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      checkFit: false,
      role: "caption",
    },
  );
}

async function slideCover(presentation) {
  const slideNo = 1;
  const data = SLIDES[0];
  const slide = presentation.slides.add();
  await addPlate(slide, slideNo);
  addShape(slide, "rect", 0, 0, W, H, TRANSPARENT, TRANSPARENT, 0, { slideNo, role: "cover contrast overlay" });
  addShape(slide, "rect", 870, 0, 410, H, PANEL_TINT, BORDER_SOFT, 1, { slideNo, role: "cover signal wall" });
  for (let i = 0; i < 11; i += 1) {
    addShape(slide, "rect", 902 + i * 28, 120 + (i % 4) * 31, 14, 250 - (i % 5) * 28, i % 2 ? "#006B4F66" : "#B018755A", TRANSPARENT, 0, {
      slideNo,
      role: "cover waveform columns",
    });
  }
  addText(slide, slideNo, "VIDEO  ->  SIGNAL  ->  EMOTION", 910, 512, 276, 24, {
    size: 12,
    color: ACCENT,
    bold: true,
    face: MONO_FACE,
    role: "cover signal label",
  });
  addShape(slide, "rect", 64, 86, 7, 455, ACCENT, TRANSPARENT, 0, { slideNo, role: "cover accent rule" });
  addText(slide, slideNo, data.kicker, 86, 88, 520, 26, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "kicker",
  });
  addText(slide, slideNo, data.title, 77, 133, 785, 184, {
    size: 48,
    color: TRANSPARENT,
    bold: true,
    face: TITLE_FACE,
    role: "cover title rgb shadow",
  });
  addText(slide, slideNo, data.title, 88, 126, 785, 184, {
    size: 48,
    color: TRANSPARENT,
    bold: true,
    face: TITLE_FACE,
    role: "cover title rgb shadow",
  });
  addText(slide, slideNo, data.title, 82, 130, 785, 184, {
    size: 48,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover title",
  });
  addText(slide, slideNo, data.subtitle, 86, 326, 610, 86, {
    size: 20,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover subtitle",
  });
  addShape(slide, "roundRect", 92, 462, 390, 92, PANEL_SHADOW, TRANSPARENT, 0, { slideNo, role: "cover moment panel shadow" });
  addShape(slide, "roundRect", 86, 456, 390, 92, WHITE, PANEL_LINE, 1.2, { slideNo, role: "cover moment panel" });
  addText(slide, slideNo, data.moment || "Replace with core idea", 112, 478, 336, 40, {
    size: 23,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover moment",
  });
  addShape(slide, "rect", 112, 530, 124, 4, MAGENTA, TRANSPARENT, 0, { slideNo, role: "cover moment glitch bar" });
  addShape(slide, "rect", 244, 530, 62, 4, ACID, TRANSPARENT, 0, { slideNo, role: "cover moment glitch bar" });
  addReferenceCaption(slide, slideNo);
  addNotes(slide, data.notes, data.sources);
}

async function slideCards(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, TRANSPARENT, TRANSPARENT, 0, { slideNo: idx, role: "content contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  const hasDemoFrame = Boolean(data.demoFramePath);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, hasDemoFrame ? 590 : 760);

  if (hasDemoFrame) {
    addShape(slide, "roundRect", 682, 100, 546, 310, PANEL_SHADOW, TRANSPARENT, 0, {
      slideNo: idx,
      role: "demo frame panel shadow",
    });
    addShape(slide, "roundRect", 674, 92, 546, 310, WHITE, PANEL_LINE, 1.2, {
      slideNo: idx,
      role: "demo frame panel",
    });
    addShape(slide, "rect", 695, 112, 128, 4, MAGENTA, TRANSPARENT, 0, { slideNo: idx, role: "demo frame glitch strip" });
    addShape(slide, "rect", 835, 112, 54, 4, ACID, TRANSPARENT, 0, { slideNo: idx, role: "demo frame glitch strip" });
    await addImage(
      slide,
      idx,
      {
        path: data.demoFramePath,
        fit: "contain",
        alt: "Annotated crowd-analysis frame with detection boxes",
      },
      { left: 682, top: 100, width: 530, height: 294 },
      "demo frame",
      data.demoFramePath,
    );
  }

  const cards = data.cards?.length
    ? data.cards
    : [
        ["Replace", "Add a specific, sourced point for this slide."],
        ["Author", "Use native PowerPoint chart objects for charts; use deterministic geometry for cards and callouts."],
        ["Verify", "Render previews, inspect them at readable size, and fix actionable layout issues within 3 total render loops."],
      ];
  const cols = Math.min(3, cards.length);
  const cardW = (1114 - (cols - 1) * 24) / cols;
  const iconKinds = ["signal", "flow", "layers"];
  for (let cardIdx = 0; cardIdx < cols; cardIdx += 1) {
    const [label, body] = cards[cardIdx];
    const x = 84 + cardIdx * (cardW + 24);
    addCard(slide, idx, x, 426, cardW, 176, label, body, { iconKind: iconKinds[cardIdx % iconKinds.length] });
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideMetrics(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, TRANSPARENT, TRANSPARENT, 0, { slideNo: idx, role: "metrics contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 700);
  const metrics = data.metrics || [
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
  ];
  const accents = [ACCENT, GOLD, CORAL];
  for (let metricIdx = 0; metricIdx < Math.min(3, metrics.length); metricIdx += 1) {
    const [metric, label, note] = metrics[metricIdx];
    addMetricCard(slide, idx, 92 + metricIdx * 370, 404, 330, 174, metric, label, note, accents[metricIdx % accents.length]);
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function createDeck() {
  await ensureDirs();
  if (!SLIDES.length) {
    throw new Error("SLIDES must contain at least one slide.");
  }
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  await slideCover(presentation);
  for (let idx = 2; idx <= SLIDES.length; idx += 1) {
    const data = SLIDES[idx - 1];
    if (data.metrics) {
      await slideMetrics(presentation, idx);
    } else {
      await slideCards(presentation, idx);
    }
  }
  return presentation;
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function writeInspectArtifact(presentation) {
  inspectRecords.unshift({
    kind: "deck",
    id: DECK_ID,
    slideCount: presentation.slides.count,
    slideSize: { width: W, height: H },
  });
  presentation.slides.items.forEach((slide, index) => {
    inspectRecords.splice(index + 1, 0, {
      kind: "slide",
      slide: index + 1,
      id: slide?.id || `slide-${index + 1}`,
    });
  });
  const lines = inspectRecords.map((record) => JSON.stringify(record)).join("\n") + "\n";
  await fs.writeFile(INSPECT_PATH, lines, "utf8");
}

async function currentRenderLoopCount() {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  if (!(await pathExists(logPath))) return 0;
  const previous = await fs.readFile(logPath, "utf8");
  return previous.split(/\r?\n/).filter((line) => line.trim()).length;
}

async function nextRenderLoopNumber() {
  return (await currentRenderLoopCount()) + 1;
}

async function appendRenderVerifyLoop(presentation, previewPaths, pptxPath) {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  const priorCount = await currentRenderLoopCount();
  const record = {
    kind: "render_verify_loop",
    deckId: DECK_ID,
    loop: priorCount + 1,
    maxLoops: MAX_RENDER_VERIFY_LOOPS,
    capReached: priorCount + 1 >= MAX_RENDER_VERIFY_LOOPS,
    timestamp: new Date().toISOString(),
    slideCount: presentation.slides.count,
    previewCount: previewPaths.length,
    previewDir: PREVIEW_DIR,
    inspectPath: INSPECT_PATH,
    pptxPath,
  };
  await fs.appendFile(logPath, JSON.stringify(record) + "\n", "utf8");
  return record;
}

async function verifyAndExport(presentation) {
  await ensureDirs();
  const nextLoop = await nextRenderLoopNumber();
  if (nextLoop > MAX_RENDER_VERIFY_LOOPS) {
    throw new Error(
      `Render/verify/fix loop cap reached: ${MAX_RENDER_VERIFY_LOOPS} total renders are allowed. ` +
        "Do not rerender; note any remaining visual issues in the final response.",
    );
  }
  await writeInspectArtifact(presentation);
  const previewPaths = [];
  for (let idx = 0; idx < presentation.slides.items.length; idx += 1) {
    const slide = presentation.slides.items[idx];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    const previewPath = path.join(PREVIEW_DIR, `slide-${String(idx + 1).padStart(2, "0")}.png`);
    await saveBlobToFile(preview, previewPath);
    previewPaths.push(previewPath);
  }
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  const pptxPath = path.join(OUT_DIR, "output.pptx");
  await pptxBlob.save(pptxPath);
  const loopRecord = await appendRenderVerifyLoop(presentation, previewPaths, pptxPath);
  return { pptxPath, loopRecord };
}

const presentation = await createDeck();
const result = await verifyAndExport(presentation);
console.log(result.pptxPath);
