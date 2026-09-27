"""YouTube yükleme izni için kalıcı yenileme anahtarı (refresh token) üretir.

Bunu KENDİ BİLGİSAYARINDA bir kez çalıştır:
  1. Google Cloud'dan "Desktop app" türündeki OAuth istemcisinin JSON dosyasını indir,
     bu klasöre client_secret.json adıyla koy.
  2. pip install google-auth-oauthlib
  3. python tools/get_refresh_token.py
  4. Açılan tarayıcıda kanalın bağlı olduğu Google hesabını seç ve izin ver.
  5. Ekrana yazılan üç değeri GitHub > Settings > Secrets and variables > Actions'a ekle.

(Python kurmak istemezsen README'deki "OAuth Playground" yolunu kullan.)
"""
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
secret = Path(__file__).with_name("client_secret.json")
if not secret.exists():
    secret = Path("client_secret.json")

flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\nBu üç değeri GitHub Secrets'a ekle:\n")
print(f"YT_CLIENT_ID      = {creds.client_id}")
print(f"YT_CLIENT_SECRET  = {creds.client_secret}")
print(f"YT_REFRESH_TOKEN  = {creds.refresh_token}")
