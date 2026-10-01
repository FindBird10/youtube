"""Yayın kaydı birleştirme: çalıştırmanın kaydını (yerel) uzak main'deki kayıtla birleştirir.

Kullanım: python tools/merge_state.py <bizim_published.json> <bizim_blocked.json|->
Çalışma dizini uzak main'e sıfırlanmış olmalı; sonuç state/ altına yazılır.
"""
import json
import sys
from pathlib import Path

ours_pub = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pub_path = Path("state/published.json")
theirs = json.loads(pub_path.read_text(encoding="utf-8")) if pub_path.exists() else []
seen = {x["slug"] for x in theirs}
merged = theirs + [x for x in ours_pub if x["slug"] not in seen]
pub_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if len(sys.argv) > 2 and sys.argv[2] != "-" and Path(sys.argv[2]).exists():
    ours_bl = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    bl_path = Path("state/blocked_tokens.json")
    theirs_bl = json.loads(bl_path.read_text(encoding="utf-8")) if bl_path.exists() else {}
    theirs_bl.update(ours_bl)
    bl_path.write_text(json.dumps(theirs_bl, indent=2) + "\n", encoding="utf-8")
print(f"birleştirildi: {len(merged)} kayıt ({len(merged) - len(theirs)} yeni)")
