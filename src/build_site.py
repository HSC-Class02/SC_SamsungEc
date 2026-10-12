import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/"data/financial_metrics.csv"
site=ROOT/"dashboard"
site.mkdir(exist_ok=True)
if data.exists():
    df=pd.read_csv(data)
    records=df.where(pd.notna(df),None).to_dict(orient="records")
else: records=[]
(site/"data.json").write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
