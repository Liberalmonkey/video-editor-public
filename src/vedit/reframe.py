"""Yatay çekimi dikeye (9:16) çevirirken yüz takipli kırpma yolu.

OpenCV YuNet yüz tespiti (library/models/…yunet….onnx, 230 KB; OpenCV 5'te Haar kaldırıldı) → en büyük yüzün yatay merkezi → ölü bölge + EMA
yumuşatma (kameraman hissi: küçük kaymalarda kıpırdamaz) → `object-position` yüzdesi.
Çıktı: build/reframe_<WxH>.json  {"path": [{"t": kaynak_saniye, "pos": 0–100}]}
"""

from __future__ import annotations

import json
from pathlib import Path

from .tembel import Tembel

cv2 = Tembel("cv2")  # WHY: Stüdyo açılışında yüklenmesin (ADR 0050)

from . import paths

YUNET = paths.LIBRARY / "models" / "face_detection_yunet_2023mar.onnx"


def object_pos(center: float, src_w: int, src_h: int, dst_w: int, dst_h: int) -> float:
    """Yüz merkezi (0–1) → cover kırpmada object-position x yüzdesi."""
    scale = max(dst_w / src_w, dst_h / src_h)
    vw = src_w * scale
    if vw - dst_w < 1:
        return 50.0
    p = (center * vw - dst_w / 2) / (vw - dst_w)
    return round(min(max(p, 0.0), 1.0) * 100, 1)


def run(root: Path, src_rel: str, dst_w: int, dst_h: int, *, step: float = 0.25, deadzone: float = 0.05,
        smooth: float = 0.25) -> Path:
    src = paths.pj(root, src_rel)
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    every = max(1, int(round(fps * step)))
    scale = 480 / sw
    dh = int(sh * scale)
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (480, dh), score_threshold=0.75)
    raw: list[tuple[float, float | None]] = []
    for i in range(n):
        ok = cap.grab()
        if not ok:
            break
        if i % every:
            continue
        ok, frame = cap.retrieve()
        if not ok:
            continue
        _, faces = det.detect(cv2.resize(frame, (480, dh)))
        if faces is not None and len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])[:4]
            raw.append((i / fps, float(x + w / 2) / 480))
        else:
            raw.append((i / fps, None))
    cap.release()
    # Boşlukları doldur, ölü bölge + EMA
    path, cur, target = [], None, 0.5
    known = [c for _, c in raw if c is not None]
    cur = known[0] if known else 0.5
    for t, c in raw:
        if c is not None and abs(c - target) > deadzone:
            target = c
        cur = cur + (target - cur) * smooth
        path.append({"t": round(t, 3), "pos": object_pos(cur, sw, sh, dst_w, dst_h)})
    # Gereksiz noktaları at (pozisyon değişmiyorsa)
    slim = [p for i, p in enumerate(path) if i == 0 or i == len(path) - 1 or abs(p["pos"] - path[i - 1]["pos"]) >= 0.4]
    out = root / "build" / f"reframe_{dst_w}x{dst_h}.json"
    out.write_text(json.dumps({"src": src_rel, "target": [dst_w, dst_h], "faces": len(known), "samples": len(raw),
                               "path": slim}, indent=1), encoding="utf-8")
    return out
