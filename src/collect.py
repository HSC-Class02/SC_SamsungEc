import json, os, time
from pathlib import Path
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
API = "https://opendart.fss.or.kr/api"
KEY = os.environ.get("DART_API_KEY", "").strip()
if not KEY:
    raise SystemExit("DART_API_KEY 환경변수가 없습니다. GitHub Actions Secret을 설정하세요.")

company = json.loads((ROOT / "config/company.json").read_text(encoding="utf-8"))
corp_code = company["corp_code"]
start_year = int(company.get("start_year", 2010))
raw_dir = ROOT / "data/raw"
raw_dir.mkdir(parents=True, exist_ok=True)
rows = []

for year in range(start_year, pd.Timestamp.now().year + 1):
    for code, label in [("11011","annual"),("11012","half-year"),("11013","quarterly"),("11014","quarterly")]:
        params = {"crtfc_key": KEY, "corp_code": corp_code, "bsns_year": str(year), "reprt_code": code}
        try:
            r = requests.get(f"{API}/fnlttSinglAcntAll.json", params={**params, "fs_div":"CFS"}, timeout=45)
            r.raise_for_status()
            payload = r.json()
            if payload.get("status") == "013":
                # No data for this year/report; not an error.
                continue
            if payload.get("status") != "000":
                print(f"Skip {year} {code}: {payload.get('status')} {payload.get('message')}")
                continue
            (raw_dir / f"{year}_{code}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            for item in payload.get("list", []):
                item["year"] = year
                item["report_code"] = code
                item["period_type"] = label
                rows.append(item)
            time.sleep(0.15)
        except requests.RequestException as e:
            print(f"Request failed {year}/{code}: {e}")

# Fallback to separate financial statements if consolidated data is unavailable for all years.
if not rows:
    for year in range(start_year, pd.Timestamp.now().year + 1):
        for code, label in [("11011","annual"),("11012","half-year"),("11013","quarterly"),("11014","quarterly")]:
            try:
                r = requests.get(f"{API}/fnlttSinglAcntAll.json", params={"crtfc_key":KEY,"corp_code":corp_code,"bsns_year":str(year),"reprt_code":code,"fs_div":"OFS"}, timeout=45)
                payload = r.json()
                if payload.get("status") == "000":
                    for item in payload.get("list", []):
                        item.update(year=year, report_code=code, period_type=label)
                        rows.append(item)
                time.sleep(0.15)
            except Exception as e:
                print(f"Fallback failed {year}/{code}: {e}")

out = ROOT / "data"
out.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(out / "dart_accounts.csv", index=False, encoding="utf-8-sig")
print(f"Saved {len(rows)} account rows")
