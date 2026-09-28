import io
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/company.json"
METRICS = ROOT / "config/metrics.json"
DATA = ROOT / "data"
RAW = DATA / "raw"
DATA.mkdir(exist_ok=True)
RAW.mkdir(exist_ok=True)

BASE = "https://opendart.fss.or.kr/api"
REPORT_CODES = {"11011":"annual","11012":"half-year","11013":"quarterly","11014":"quarterly"}

def api_key():
    key = os.getenv("DART_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DART_API_KEY GitHub Secret/environment variable is required.")
    return key

def get_json(endpoint, params):
    params = dict(params)
    params["crtfc_key"] = api_key()
    r = requests.get(f"{BASE}/{endpoint}.json", params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "000":
        raise RuntimeError(f"DART API {endpoint}: {data.get('status')} {data.get('message')}")
    return data

def clean_num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "nan", "None"):
        return None
    s = s.replace("(", "-").replace(")", "")
    try:
        return float(s)
    except ValueError:
        return None

def filing_list(year):
    out = []
    for code, kind in REPORT_CODES.items():
        try:
            d = get_json("list", {
                "corp_code": COMPANY["corp_code"],
                "bgn_de": f"{year}0101",
                "end_de": f"{year}1231",
                "pblntf_ty": "A",
                "page_no": 1,
                "page_count": 100
            })
        except Exception:
            continue
        for item in d.get("list", []):
            title = item.get("report_nm","")
            if code == "11011" and "사업보고서" not in title:
                continue
            if code == "11012" and "반기보고서" not in title:
                continue
            if code == "11013" and "분기보고서" not in title:
                continue
            if code == "11014" and "분기보고서" not in title:
                continue
            if "첨부" in title:
                continue
            out.append({
                "year": year,
                "report_type": kind,
                "reprt_code": code,
                "report_nm": title,
                "rcept_no": item.get("rcept_no"),
                "rcept_dt": item.get("rcept_dt"),
                "report_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no')}"
            })
    # deduplicate by receipt number
    return list({x["rcept_no"]: x for x in out if x["rcept_no"]}.values())

def financial_api(year, code):
    data = get_json("fnlttSinglAcntAll", {
        "corp_code": COMPANY["corp_code"],
        "bsns_year": str(year),
        "reprt_code": code,
        "fs_div": COMPANY["fs_div"]
    })
    return data.get("list", [])

def pick_value(rows, candidates, cumulative=False):
    normalized = {re.sub(r"\s+", "", c) for c in candidates}
    matches = []
    for row in rows:
        nm = re.sub(r"\s+", "", str(row.get("account_nm","")))
        if nm in normalized or any(c in nm for c in normalized):
            key = "thstrm_add_amount" if cumulative else "thstrm_amount"
            value = clean_num(row.get(key))
            if value is None:
                value = clean_num(row.get("thstrm_amount"))
            if value is not None:
                matches.append((int(row.get("ord") or 999999), value, row))
    if not matches:
        return None, None
    matches.sort(key=lambda x:x[0])
    return matches[0][1], matches[0][2]

def parse_structured(year, code):
    rows = financial_api(year, code)
    metric_map = json.load(open(METRICS, encoding="utf-8"))
    result = {}
    meta = {}
    for section in metric_map.values():
        for metric, candidates in section.items():
            cumulative = code in ("11012","11013","11014") and metric in metric_map["income_statement"]
            val, row = pick_value(rows, candidates, cumulative=cumulative)
            result[metric] = val
            if row:
                meta[metric+"_account"] = row.get("account_nm")
                meta["currency"] = row.get("currency")
    result.update({
        "year": year,
        "report_type": REPORT_CODES[code],
        "reprt_code": code,
        "source": "OpenDART structured financial API"
    })
    result.update(meta)
    return result

def save_original_report(receipt):
    target = RAW / f"{receipt}.zip"
    if target.exists():
        return str(target)
    params = {"crtfc_key": api_key(), "rcept_no": receipt}
    r = requests.get(f"{BASE}/document.xml", params=params, timeout=120)
    r.raise_for_status()
    target.write_bytes(r.content)
    return str(target)

def fallback_old_year(year, filings):
    # OpenDART structured financial APIs begin in 2015.
    # For 2010-2014, preserve original DART report archives and leave
    # normalized financial values blank rather than fabricating numbers.
    rows = []
    for f in filings:
        save_original_report(f["rcept_no"])
        rows.append({
            "year": year,
            "report_type": f["report_type"],
            "reprt_code": f["reprt_code"],
            "rcept_no": f["rcept_no"],
            "report_nm": f["report_nm"],
            "rcept_dt": f["rcept_dt"],
            "report_url": f["report_url"],
            "source": "DART original report archive",
            "note": "2010-2014 requires original-report XML/XBRL normalization; archive retained for parser extension."
        })
    return rows

def ratio_frame(df):
    def safe(a,b):
        return (a/b*100) if pd.notna(a) and pd.notna(b) and b != 0 else None
    df = df.copy()
    df["영업이익률"] = df.apply(lambda r:safe(r["영업이익"],r["매출액"]),axis=1)
    df["순이익률"] = df.apply(lambda r:safe(r["당기순이익"],r["매출액"]),axis=1)
    df["ROA"] = df.apply(lambda r:safe(r["당기순이익"],r["자산총계"]),axis=1)
    df["ROE"] = df.apply(lambda r:safe(r["당기순이익"],r["자본총계"]),axis=1)
    df["부채비율"] = df.apply(lambda r:safe(r["부채총계"],r["자본총계"]),axis=1)
    df["유동비율"] = df.apply(lambda r:safe(r["유동자산"],r["유동부채"]),axis=1)
    df["자기자본비율"] = df.apply(lambda r:safe(r["자본총계"],r["자산총계"]),axis=1)
    for metric in ["매출액","영업이익","당기순이익"]:
        df[f"{metric} 증가율"] = df.groupby("report_type")[metric].pct_change()*100
    return df

def main():
    global COMPANY
    COMPANY = json.load(open(CONFIG, encoding="utf-8"))
    all_fin = []
    all_filings = []
    current_year = datetime.now().year
    for year in range(COMPANY["start_year"], current_year + 1):
        filings = filing_list(year)
        all_filings.extend(filings)
        if year < 2015:
            all_fin.extend(fallback_old_year(year, filings))
            continue
        for code in REPORT_CODES:
            try:
                row = parse_structured(year, code)
                match = next((f for f in filings if f["reprt_code"] == code), None)
                if match:
                    row.update({"rcept_no":match["rcept_no"],"rcept_dt":match["rcept_dt"],"report_nm":match["report_nm"],"report_url":match["report_url"]})
                all_fin.append(row)
            except Exception as e:
                print(f"[WARN] {year} {code}: {e}")

    df = pd.DataFrame(all_fin)
    if df.empty:
        raise RuntimeError("No financial data was returned.")
    for col in ["매출액","영업이익","당기순이익","자산총계","부채총계","자본총계","유동자산","유동부채","영업현금흐름","투자현금흐름","재무현금흐름","유형자산취득"]:
        if col not in df:
            df[col] = None
    cols = ["year","report_type","reprt_code","rcept_no","rcept_dt","report_nm","report_url",
            "매출액","영업이익","당기순이익","자산총계","부채총계","자본총계","유동자산","유동부채",
            "영업현금흐름","투자현금흐름","재무현금흐름","유형자산취득","source","note"]
    for c in cols:
        if c not in df:
            df[c] = None
    df = df[cols].sort_values(["year","report_type"]).drop_duplicates(["year","reprt_code"], keep="last")
    df.to_csv(DATA/"financials.csv", index=False, encoding="utf-8-sig")

    ratios = ratio_frame(df)
    ratios.to_csv(DATA/"ratios.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame(all_filings).drop_duplicates("rcept_no").sort_values("rcept_dt").to_csv(
        DATA/"filings.csv", index=False, encoding="utf-8-sig"
    )
    print(f"Saved {len(df)} normalized rows and {len(all_filings)} filing records.")

if __name__ == "__main__":
    main()
