import json
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT/"config/metrics.json").read_text(encoding="utf-8"))
source = ROOT/"data/dart_accounts.csv"
out = ROOT/"data/financial_metrics.csv"
if not source.exists():
    raise SystemExit("data/dart_accounts.csv가 없습니다. 먼저 src/collect.py를 실행하세요.")
df = pd.read_csv(source).fillna("")
if df.empty:
    pd.DataFrame().to_csv(out,index=False,encoding="utf-8-sig"); raise SystemExit("DART 데이터가 비어 있습니다.")

def num(v):
    try:
        s=str(v).replace(",","").strip()
        return float(s) if s not in ("","-","nan","None") else np.nan
    except Exception: return np.nan

def choose(group, aliases):
    # Prefer consolidated statement values and current-period amounts.
    for alias in aliases:
        hit = group[group["account_nm"].astype(str).str.strip().str.casefold() == alias.casefold()]
        if not hit.empty:
            for col in ["thstrm_amount","thstrm_add_amount"]:
                if col in hit:
                    vals=hit[col].map(num).dropna()
                    if len(vals): return vals.iloc[0]
    return np.nan

rows=[]
for (year, code, ptype), g in df.groupby(["year","report_code","period_type"], dropna=False):
    rec={"year":int(float(year)),"report_code":str(code),"period_type":ptype}
    for key, aliases in cfg["fields"].items(): rec[key]=choose(g, aliases)
    rec["operating_margin_pct"]=rec["operating_profit"]/rec["revenue"]*100 if pd.notna(rec["revenue"]) and rec["revenue"] else np.nan
    rec["net_margin_pct"]=rec["net_income"]/rec["revenue"]*100 if pd.notna(rec["revenue"]) and rec["revenue"] else np.nan
    rec["debt_to_equity_pct"]=rec["total_liabilities"]/rec["total_equity"]*100 if pd.notna(rec["total_equity"]) and rec["total_equity"] else np.nan
    rec["current_ratio_pct"]=rec["current_assets"]/rec["current_liabilities"]*100 if pd.notna(rec["current_liabilities"]) and rec["current_liabilities"] else np.nan
    rec["roa_pct"]=rec["net_income"]/rec["total_assets"]*100 if pd.notna(rec["total_assets"]) and rec["total_assets"] else np.nan
    rec["roe_pct"]=rec["net_income"]/rec["total_equity"]*100 if pd.notna(rec["total_equity"]) and rec["total_equity"] else np.nan
    rows.append(rec)
result=pd.DataFrame(rows).sort_values(["year","report_code"])
# Growth is calculated only against the same report type in the previous year.
result["revenue_growth_pct"]=result.groupby("report_code")["revenue"].pct_change()*100
result.to_csv(out,index=False,encoding="utf-8-sig")
print(f"Saved {len(result)} financial metric rows")
