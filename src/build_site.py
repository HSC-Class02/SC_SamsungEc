import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
data_csv = ROOT / "data" / "financial_metrics.csv"
site_dir = ROOT / "dashboard"
site_dir.mkdir(exist_ok=True)

if data_csv.exists():
    try:
        df = pd.read_csv(data_csv)
        # NaN 값을 None으로 안전하게 변환 후 dict로 변환
        records = df.where(pd.notna(df), None).to_dict(orient="records")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        records = []
else:
    print(f"Warning: {data_csv} does not exist. Creating empty data.json")
    records = []

# 대시보드가 읽어갈 data.json 생성
json_path = site_dir / "data.json"
json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Successfully generated {json_path} with {len(records)} records.")
