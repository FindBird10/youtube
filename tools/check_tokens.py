"""Her kanalın token'ının hangi YouTube kanalına ait olduğunu yükleme yapmadan gösterir.

Token youtube.readonly iznine sahipse kanal adı okunur; yalnızca upload izni varsa
"doğrulanamadı" yazar. Token'ın kendisi yazdırılmaz.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
from channels import CHANNELS, check_channel  # noqa: E402
from upload import _service, have_credentials, token_fingerprint  # noqa: E402

from googleapiclient.errors import HttpError  # noqa: E402

for ch, cfg in CHANNELS.items():
    if not have_credentials(ch):
        print(f"{ch}: token yok")
        continue
    fp = token_fingerprint(ch)
    try:
        items = _service(ch).channels().list(part="snippet", mine=True).execute().get("items", [])
        if not items:
            print(f"{ch}: token geçerli ama hesapta kanal yok (iz {fp})")
            continue
        title, cid = items[0]["snippet"]["title"], items[0]["id"]
        problem = check_channel(ch, title)
        print(f"{ch}: '{title}' ({cid}) iz {fp} → " + ("YANLIŞ: " + problem if problem else "DOĞRU"))
    except HttpError as e:
        if e.resp.status in (401, 403):
            import re
            reason = ",".join(sorted(set(re.findall(r"'reason': '([^']+)'", str(e))))) or str(e)[:160]
            print(f"{ch}: kanal adı okunamadı (iz {fp}) [{e.resp.status} {reason}]")
        else:
            print(f"{ch}: hata {e.resp.status}: {str(e)[:200]}")
    except Exception as e:
        print(f"{ch}: hata {type(e).__name__}: {str(e)[:200]}")
