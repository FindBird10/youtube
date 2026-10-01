"""Görseldeki en belirgin yüzü bulur (OpenCV YuNet; model: assets/models, MIT lisanslı).

Dikey (9:16) kırpmada karakterin yüzü kadraj dışında kalmasın diye kullanılır.
focus(path) → (x, y, h): yüz merkezinin görsele oranla konumu ve yüz yüksekliğinin
görsel yüksekliğine oranı. Yüz bulunamazsa ya da OpenCV yoksa None.
"""
from __future__ import annotations

from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / "assets" / "models" / "face_detection_yunet_2023mar.onnx"
_cache: dict[str, tuple[float, float, float] | None] = {}


def focus(path: Path) -> tuple[float, float, float] | None:
    key = str(path)
    if key in _cache:
        return _cache[key]
    result = None
    try:
        import cv2

        img = cv2.imread(key)
        if img is not None:
            h, w = img.shape[:2]
            scale = 1280 / max(h, w) if max(h, w) > 1280 else 1.0
            small = cv2.resize(img, (int(w * scale), int(h * scale))) if scale < 1 else img
            sh, sw = small.shape[:2]
            det = cv2.FaceDetectorYN.create(str(MODEL), "", (sw, sh), 0.7, 0.3, 50)
            _, faces = det.detect(small)
            if faces is not None and len(faces):
                # en büyük ve en emin yüz
                x, y, bw, bh = max(faces, key=lambda f: f[2] * f[3] * f[14])[:4]
                result = (float((x + bw / 2) / sw), float((y + bh / 2) / sh), float(bh / sh))
    except Exception as e:  # OpenCV yoksa ya da görsel okunamazsa ortadan kırpılır
        print(f"[faces] {Path(key).name}: {type(e).__name__}: {e}", flush=True)
    _cache[key] = result
    return result
