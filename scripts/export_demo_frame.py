from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def find_video_path(root: Path, set_id: str) -> Path:
    for p in sorted((root / "data/raw/videos").glob(f"{set_id}.*")):
        if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
            return p
    raise FileNotFoundError(f"No video found for {set_id}")


def phone_boxes(roi_bgr: np.ndarray) -> tuple[list[tuple[int, int, int, int]], float]:
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    bright_neutral = cv2.inRange(hsv, (0, 0, 210), (179, 95, 255))
    bright_blue = cv2.inRange(hsv, (90, 40, 170), (140, 255, 255))
    mask = cv2.bitwise_or(bright_neutral, bright_blue)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 8 or area > 2500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0:
            continue
        ratio = w / float(h)
        if 0.35 <= ratio <= 1.2:
            boxes.append((x, y, w, h))

    roi_pixels = roi_bgr.shape[0] * roi_bgr.shape[1]
    proxy = float(len(boxes)) / max(roi_pixels / 12000.0, 1.0)
    return boxes, proxy


def face_boxes(gray_roi: np.ndarray) -> list[tuple[int, int, int, int]]:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        return []

    faces = face_cascade.detectMultiScale(
        gray_roi,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(24, 24),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export annotated demo frame")
    parser.add_argument("--set-id", default="set_1_unknown_dj")
    parser.add_argument("--t-sec", type=int, default=2830)
    parser.add_argument("--crowd-top-ratio", type=float, default=0.4)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    video_path = find_video_path(root, args.set_id)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {video_path}")

    cap.set(cv2.CAP_PROP_POS_MSEC, max(args.t_sec - 10, 0) * 1000.0)
    ok_prev, prev = cap.read()

    cap.set(cv2.CAP_PROP_POS_MSEC, args.t_sec * 1000.0)
    ok_cur, frame = cap.read()
    cap.release()

    if not ok_cur or frame is None:
        raise RuntimeError(f"Could not read frame at t={args.t_sec}s")

    h, w = frame.shape[:2]
    y0 = int(h * args.crowd_top_ratio)

    roi = frame[y0:, :].copy()
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    movement = 0.0
    lighting_flux = 0.0
    if ok_prev and prev is not None:
        prev_roi = prev[y0:, :]
        prev_gray = cv2.cvtColor(prev_roi, cv2.COLOR_BGR2GRAY)
        if prev_gray.shape == gray.shape:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None, 0.5, 2, 15, 2, 5, 1.1, 0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            movement = float(np.mean(mag))
            diff = cv2.absdiff(prev_gray, gray)
            lighting_flux = float(np.mean(diff)) / 255.0

    p_boxes, phone_proxy = phone_boxes(roi)
    f_boxes = face_boxes(gray)

    annotated = frame.copy()

    # Crowd ROI box
    cv2.rectangle(annotated, (0, y0), (w - 1, h - 1), (255, 215, 0), 2)
    cv2.putText(
        annotated,
        "Crowd ROI",
        (12, max(y0 - 10, 24)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 215, 0),
        2,
        cv2.LINE_AA,
    )

    # Phone-like boxes
    for (x, y, bw, bh) in p_boxes:
        cv2.rectangle(annotated, (x, y + y0), (x + bw, y + bh + y0), (0, 255, 0), 2)

    # Face boxes
    for (x, y, bw, bh) in f_boxes:
        cv2.rectangle(annotated, (x, y + y0), (x + bw, y + bh + y0), (0, 0, 255), 2)

    # Legend and stats
    cv2.rectangle(annotated, (10, 10), (600, 165), (0, 0, 0), -1)
    cv2.putText(annotated, f"Set: {args.set_id}", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(annotated, f"Time: {args.t_sec}s", (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(annotated, f"Movement (raw): {movement:.3f}", (20, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(annotated, f"Lighting flux (raw): {lighting_flux:.3f}", (20, 114), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(annotated, f"Phone boxes: {len(p_boxes)} | Face boxes: {len(f_boxes)}", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    out_path = root / "data/processed/demo_frames" / f"{args.set_id}_{args.t_sec}s_annotated.jpg"
    cv2.imwrite(str(out_path), annotated)

    print(str(out_path))
    print(f"phone_boxes={len(p_boxes)} face_boxes={len(f_boxes)} movement={movement:.4f} lighting_flux={lighting_flux:.4f}")


if __name__ == "__main__":
    main()
