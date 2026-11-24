import hashlib
import io
import os
import urllib.parse
import zipfile
import requests

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
os.makedirs(BASE_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "skillhub-cli/0.2.28"})

TARGETS = [
    ("生活办事材料核验管家", "20260716.135124", "life-service-doc-verifier"),
    ("gov-assistant", "2.0.0", "gov-assistant"),
    ("视障职场文档表格无障碍转述助手", "20260716.144341", "vision-a11y-doc-narrator"),
]

for slug, ver, folder in TARGETS:
    url = f"https://skill.xfyun.cn/api/v1/skills/global/{urllib.parse.quote(slug)}/versions/{ver}/download"
    r = session.get(url, timeout=20)
    ct = r.headers.get("Content-Type", "")
    sha = hashlib.sha256(r.content).hexdigest()
    print(f"[{slug}@{ver}] status={r.status_code} bytes={len(r.content)} sha256={sha} ct={ct}")
    if r.status_code == 200 and r.content[:2] == b"PK":
        zpath = os.path.join(BASE_DIR, f"{folder}-{ver}.zip")
        with open(zpath, "wb") as f:
            f.write(r.content)
        out = os.path.join(BASE_DIR, folder)
        os.makedirs(out, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            zf.extractall(out)
            print("  Files:", zf.namelist())
    else:
        print("  Body preview:", r.text[:200])
