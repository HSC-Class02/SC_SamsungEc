# Samsung Electro-Mechanics DART Financial Agent

[![Dashboard](https://discord.com/assets/ed3a958a3bb08d4a.svg)](https://hsc-class02.github.io/SC_SamsungEc/)
[🔗 대시보드 바로가기](https://hsc-class02.github.io/SC_SamsungEc/)

삼성전기(009150)의 DART 정기보고서를 수집하고 재무수치·재무비율을 자동 계산하여 GitHub Pages 대시보드로 제공하는 프로젝트입니다.

## 범위

- 대상: 삼성전기 / 종목코드 `009150` / DART corp_code `00126371`
- 보고서: 사업보고서, 반기보고서, 1분기보고서, 3분기보고서
- 시작연도: 2010
- 2015년 이후: OpenDART 구조화 재무제표 API 사용
- 2010~2014년: DART 원문 보고서 ZIP/XML fallback
- 자동 업데이트: 매월 1일
- 대시보드: GitHub Pages
- 분석 기준: 연결재무제표(CFS) 우선

> 참고: OpenDART의 `fnlttSinglAcntAll` 구조화 재무제표 API는 2015년 이후 데이터를 제공합니다. 따라서 2010~2014년은 원문 보고서 수집/파싱 경로를 별도로 둡니다.

## 주요 산출물

- `data/financials.csv`: 주요 재무수치
- `data/ratios.csv`: 재무비율
- `data/filings.csv`: 정기보고서 목록 및 DART 접수번호
- `data/raw/`: DART 원문 ZIP 보관
- `site/index.html`: 대시보드
- `.github/workflows/update.yml`: 월 1회 수집 + Pages 배포

## API Key 설정

1. OpenDART에서 인증키를 발급합니다.
2. GitHub repository → **Settings → Secrets and variables → Actions → New repository secret**
3. Name: `DART_API_KEY`
4. Value: 발급받은 40자리 인증키
5. 저장합니다.

API 키를 코드, README, CSV, commit에 직접 입력하지 마세요.

## GitHub Pages 설정

### ZIP 업로드 후 Workflow 배치

이 ZIP에는 숨김 폴더를 넣지 않았습니다. GitHub Actions가 인식하도록 저장소에서 다음 파일을 이동하세요:

`workflow/update.yml` → `.github/workflows/update.yml`

GitHub 웹에서 `Add file → Create new file`로 `.github/workflows/update.yml`을 만든 뒤, ZIP의 `workflow/update.yml` 내용을 그대로 붙여넣어도 됩니다.


Repository → **Settings → Pages**에서 Build and deployment의 Source를 **GitHub Actions**로 선택합니다.

그 다음 Actions에서 `DART Financial Agent` workflow를 한 번 `Run workflow` 하면 수집과 Pages 배포가 진행됩니다.

대시보드 주소:
https://hsc-class02.github.io/SC_SamsungEc/

## 매월 자동 업데이트

Workflow에는 다음 cron이 설정되어 있습니다.

```text
0 0 1 * *
```

GitHub Actions의 cron은 UTC 기준이므로 한국시간으로는 매월 1일 오전 9시입니다.

## 재무지표

기본 분석 항목:

- 매출액
- 영업이익
- 당기순이익
- 자산총계
- 부채총계
- 자본총계
- 영업현금흐름
- 투자현금흐름
- 재무현금흐름
- CAPEX
- 영업이익률
- 순이익률
- ROA
- ROE
- 부채비율
- 유동비율
- 자기자본비율
- 매출액 증가율
- 영업이익 증가율
- 순이익 증가율

첨부된 재무항목 파일이 이 패키지 생성 시점에 검색되지 않아, 표준적인 핵심 재무계정과 비율을 기본값으로 구성했습니다. 파일을 추가로 주시면 `config/metrics.json`만 수정하여 정확히 맞출 수 있습니다.

## 국내 Peer Firms

삼성전기의 MLCC/수동부품 및 기판 사업과 비교할 때 참고 가능한 국내 peer 후보를 별도 표로 관리합니다.

| 기업 | 종목코드 | 주요 비교영역 |
|---|---:|---|
| 삼화콘덴서 | 001820 | MLCC / 수동부품 |
| 대덕전자 | 353200 | 반도체 패키지 기판 / PCB |
| 심텍 | 222800 | 반도체 패키지 기판 / PCB |
| 코리아써키트 | 007810 | PCB / 반도체 패키지 |
| LG이노텍 | 011070 | 전자부품 / 기판 |

Peer는 동일한 사업구조라는 뜻이 아니라, 삼성전기의 주요 사업영역과 비교분석에 활용할 수 있는 국내 상장사 후보라는 의미입니다.

## 실행

```bash
pip install -r requirements.txt
set DART_API_KEY=YOUR_KEY
python agent/update.py
```

macOS/Linux:

```bash
export DART_API_KEY=YOUR_KEY
python agent/update.py
```
