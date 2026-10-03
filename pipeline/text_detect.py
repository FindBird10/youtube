"""Karede yazı var mı? (OpenCV + PP-OCRv3 metin bulucu; model: assets/models, Apache-2.0)

text_ratio(path) → yazı kutularının kare alanına oranı (0–1). Model yoksa 0.
Fragmanlardaki başlık/tarih kartlarını ve menü (UI) görüntülerini elemek için kullanılır.
"""
from __future__ import annotations

from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / "assets" / "models" / "text_detection_ppocr.onnx"
_model = None


def _load():
    global _model
    if _model is None:
        import cv2

        m = cv2.dnn_TextDetectionModel_DB(str(MODEL))
        m.setBinaryThreshold(0.3)
        m.setPolygonThreshold(0.5)
        m.setMaxCandidates(200)
        m.setUnclipRatio(2.0)
        m.setInputParams(1.0 / 255.0, (736, 736), (122.67891434, 116.66876762, 104.00698793), True)
        _model = m
    return _model


def text_ratio(path: Path, center_x: float | None = None) -> float:
    """center_x verilirse yalnızca dikey (9:16) videoda görünecek şerit incelenir."""
    try:
        import cv2
        import numpy as np

        img = cv2.imread(str(path))
        if img is None:
            return 0.0
        h, w = img.shape[:2]
        if center_x is not None:
            cw = min(w, int(h * 9 / 16))
            x0 = int(min(max(center_x * w - cw / 2, 0), w - cw))
            img = img[:, x0:x0 + cw]
        boxes, _ = _load().detect(cv2.resize(img, (736, 736)))
        area = sum(cv2.contourArea(np.array(b, dtype=np.float32)) for b in boxes)
        return float(area / (736 * 736))
    except Exception as e:
        print(f"[text_detect] {Path(path).name}: {type(e).__name__}: {e}", flush=True)
        return 0.0
