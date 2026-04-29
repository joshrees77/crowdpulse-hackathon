from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from .settings import PEAKS_DIR, SCORES_DIR, SET_SUMMARY_PATH, ensure_dirs


def _normalize_series(values: pd.Series) -> pd.Series:
    min_v = values.min()
    max_v = values.max()
    if max_v - min_v < 1e-9:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - min_v) / (max_v - min_v)


def _downscale_for_speed(image: np.ndarray, max_width: int = 640) -> np.ndarray:
    """Downscale large frames to keep laptop runtime manageable."""
    h, w = image.shape[:2]
    if w <= max_width:
        return image
    scale = max_width / float(w)
    new_h = max(int(h * scale), 1)
    return cv2.resize(image, (max_width, new_h), interpolation=cv2.INTER_AREA)


def _phone_screen_proxy(roi_bgr: np.ndarray) -> float:
    """
    Approximate phone-filming intensity using bright, screen-like blobs.

    Heuristic only: finds bright rectangles in the crowd region.
    """
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    # Bright/low-saturation and bright-blue blobs are common in screens.
    bright_neutral = cv2.inRange(hsv, (0, 0, 210), (179, 95, 255))
    bright_blue = cv2.inRange(hsv, (90, 40, 170), (140, 255, 255))
    mask = cv2.bitwise_or(bright_neutral, bright_blue)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    screen_like = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 8 or area > 2500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0:
            continue
        ratio = w / float(h)
        if 0.35 <= ratio <= 1.2:
            screen_like += 1

    roi_pixels = roi_bgr.shape[0] * roi_bgr.shape[1]
    return float(screen_like) / max(roi_pixels / 12000.0, 1.0)


def _texture_density_proxy(gray_roi: np.ndarray) -> float:
    """
    Approximate crowd density via edge density.

    More visible people and clothing detail usually increase edge coverage.
    """
    edges = cv2.Canny(gray_roi, 80, 160)
    return float(np.mean(edges > 0))


def _lighting_flux_proxy(gray_roi: np.ndarray, prev_gray_roi: np.ndarray | None) -> float:
    """
    Approximate lighting/strobe dynamics with inter-frame luminance change.
    """
    if prev_gray_roi is None or prev_gray_roi.shape != gray_roi.shape:
        return 0.0
    diff = cv2.absdiff(gray_roi, prev_gray_roi)
    return float(np.mean(diff)) / 255.0


def _motion_change_ratio(gray_roi: np.ndarray, prev_gray_roi: np.ndarray | None) -> float:
    """
    Percent of pixels with notable intensity change since previous sample.
    """
    if prev_gray_roi is None or prev_gray_roi.shape != gray_roi.shape:
        return 0.0
    diff = cv2.absdiff(gray_roi, prev_gray_roi)
    moving = diff > 24
    return float(np.mean(moving))


def _load_face_cascade() -> cv2.CascadeClassifier | None:
    """
    Load Haar face detector if available in this OpenCV build.
    """
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        if detector.empty():
            return None
        return detector
    except Exception:
        return None


def _face_presence_proxy(gray_roi: np.ndarray, face_cascade: cv2.CascadeClassifier | None) -> tuple[float, float]:
    """
    Return (face_count, face_area_ratio) in the crowd ROI.

    This is detection-only. No identity recognition is performed.
    """
    if face_cascade is None:
        return 0.0, 0.0

    faces = face_cascade.detectMultiScale(
        gray_roi,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(24, 24),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    if len(faces) == 0:
        return 0.0, 0.0

    roi_pixels = float(gray_roi.shape[0] * gray_roi.shape[1])
    total_face_area = sum(float(w * h) for (_, _, w, h) in faces)
    return float(len(faces)), float(total_face_area / max(roi_pixels, 1.0))


def analyze_set_video(
    set_id: str,
    video_path: Path,
    interval_seconds: int = 10,
    crowd_crop_top_ratio: float = 0.4,
    enable_face_metrics: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze one set and return (timeline_df, peaks_df)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration_seconds = frame_count / fps if fps else 0

    timestamps = np.arange(0, max(duration_seconds, interval_seconds), interval_seconds)

    prev_gray = None
    face_cascade = _load_face_cascade() if enable_face_metrics else None
    rows: list[dict] = []

    for t in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        h, w = frame.shape[:2]
        y0 = int(h * crowd_crop_top_ratio)
        roi = frame[y0:, :]
        roi = _downscale_for_speed(roi, max_width=640)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        movement = 0.0
        if prev_gray is not None and prev_gray.shape == gray.shape:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray,
                gray,
                None,
                0.5,
                2,
                15,
                2,
                5,
                1.1,
                0,
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            movement = float(np.mean(mag))

        phone_proxy = _phone_screen_proxy(roi)
        texture_density = _texture_density_proxy(gray)
        lighting_flux = _lighting_flux_proxy(gray, prev_gray)
        motion_change_ratio = _motion_change_ratio(gray, prev_gray)
        face_count, face_area_ratio = _face_presence_proxy(gray, face_cascade)
        prev_gray = gray

        rows.append(
            {
                "set_id": set_id,
                "t_sec": int(t),
                "movement_raw": movement,
                "phone_proxy_raw": phone_proxy,
                "texture_density_raw": texture_density,
                "lighting_flux_raw": lighting_flux,
                "motion_change_raw": motion_change_ratio,
                "face_count_raw": face_count,
                "face_area_ratio_raw": face_area_ratio,
            }
        )

    cap.release()

    if not rows:
        raise RuntimeError(f"No frames analyzed for {set_id}")

    timeline = pd.DataFrame(rows)
    timeline["movement_norm"] = _normalize_series(timeline["movement_raw"])
    timeline["phone_proxy_norm"] = _normalize_series(timeline["phone_proxy_raw"])
    timeline["texture_density_norm"] = _normalize_series(timeline["texture_density_raw"])
    timeline["lighting_flux_norm"] = _normalize_series(timeline["lighting_flux_raw"])
    timeline["motion_change_norm"] = _normalize_series(timeline["motion_change_raw"])
    timeline["face_count_norm"] = _normalize_series(timeline["face_count_raw"])
    timeline["face_area_ratio_norm"] = _normalize_series(timeline["face_area_ratio_raw"])

    # Backward-compatible baseline metric.
    timeline["crowd_energy_v1"] = 0.7 * timeline["movement_norm"] + 0.3 * timeline["phone_proxy_norm"]

    # Expanded score for richer hackathon insights.
    timeline["crowd_energy"] = (
        0.45 * timeline["movement_norm"]
        + 0.20 * timeline["phone_proxy_norm"]
        + 0.15 * timeline["lighting_flux_norm"]
        + 0.10 * timeline["motion_change_norm"]
        + 0.05 * timeline["texture_density_norm"]
        + 0.05 * timeline["face_count_norm"]
    )

    # Rolling smooth to reduce noisy spikes.
    timeline["crowd_energy_smooth"] = (
        timeline["crowd_energy"].rolling(window=5, min_periods=1, center=True).mean()
    )

    hi = timeline["crowd_energy_smooth"].quantile(0.90)
    lo = timeline["crowd_energy_smooth"].quantile(0.10)

    peaks = timeline[timeline["crowd_energy_smooth"] >= hi].copy()
    peaks["moment_type"] = "high"
    lows = timeline[timeline["crowd_energy_smooth"] <= lo].copy()
    lows["moment_type"] = "low"
    moments = pd.concat([peaks, lows], ignore_index=True).sort_values("t_sec")

    return timeline, moments


def analyze_all_sets(
    downloads_df: pd.DataFrame,
    set_metadata_df: pd.DataFrame,
    interval_seconds: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()

    score_frames = []
    peak_frames = []
    summary_rows = []

    for _, row in downloads_df.iterrows():
        if row.get("status") == "error":
            continue

        set_id = row["set_id"]
        video_path = Path(row["video_path"])
        if not video_path.exists():
            continue

        timeline, moments = analyze_set_video(
            set_id=set_id,
            video_path=video_path,
            interval_seconds=interval_seconds,
        )

        timeline_path = SCORES_DIR / f"{set_id}_scores.csv"
        moments_path = PEAKS_DIR / f"{set_id}_moments.csv"
        timeline.to_csv(timeline_path, index=False)
        moments.to_csv(moments_path, index=False)

        score_frames.append(timeline)
        peak_frames.append(moments)

        summary_rows.append(
            {
                "set_id": set_id,
                "avg_energy": float(timeline["crowd_energy_smooth"].mean()),
                "max_energy": float(timeline["crowd_energy_smooth"].max()),
                "min_energy": float(timeline["crowd_energy_smooth"].min()),
                "high_moment_count": int((moments["moment_type"] == "high").sum()),
                "low_moment_count": int((moments["moment_type"] == "low").sum()),
                "avg_movement": float(timeline["movement_norm"].mean()),
                "avg_phone_proxy": float(timeline["phone_proxy_norm"].mean()),
                "avg_lighting_flux": float(timeline["lighting_flux_norm"].mean()),
                "avg_motion_change": float(timeline["motion_change_norm"].mean()),
                "avg_texture_density": float(timeline["texture_density_norm"].mean()),
                "avg_face_presence": float(timeline["face_count_norm"].mean()),
            }
        )

    scores_df = pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame()
    peaks_df = pd.concat(peak_frames, ignore_index=True) if peak_frames else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows)

    if not summary_df.empty:
        summary_df = summary_df.merge(set_metadata_df, on="set_id", how="left")
        summary_df.to_csv(SET_SUMMARY_PATH, index=False)

    return scores_df, peaks_df, summary_df
