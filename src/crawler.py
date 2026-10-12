import os
import requests
import pandas as pd
import json

API_KEY = os.environ.get("DART_API_KEY")
CORP_CODE = "00164779" # 삼성전기 고유번호

def fetch_financial_data(year, reprt_code):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": CORP_CODE,
        "bsns_year": str(year),
        "reprt_code": reprt_code, # 11011: 사업, 11012: 반기, 11013: 1분기, 11014: 3분기
        "fs_div": "CFS" # 연결재무제표
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "000":
            return data.get("list", [])
    return []

def main():
    if not API_KEY:
        raise ValueError("DART_API_KEY가 설정되지 않았습니다.")
    
    all_data = []
    years = range(2010, 2027)
    reports = {
        "Annual": "11011",
        "Half-year": "11012",
        "Quarterly": "11013"
    }

    print("DART 재무 데이터 수집 시작...")
    for year in years:
        for r_name, r_code in reports.items():
            raw_list = fetch_financial_data(year, r_code)
            for item in raw_list:
                all_data.append({
                    "year": year,
                    "category": r_name,
                    "account_nm": item.get("account_nm"),
                    "thstrm_amount": item.get("thstrm_amount"),
                    "fs_nm": item.get("fs_nm")
                })
    
    df = pd.DataFrame(all_data)
    os.makedirs("docs/data", exist_ok=True)
    df.to_json("docs/data/financial_data.json", orient="records", force_ascii=False)
    print("데이터 수집 완료 및 저장 성공.")

if __name__ == "__main__":
    main()
