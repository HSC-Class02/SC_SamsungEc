# Samsung Electro-Mechanics | DART Financial Dashboard

[![🔗 대시보드 바로가기](https://discord.com/assets/ed3a958a3bb08d4a.svg)](https://HSC-Class02.github.io/SC_SamsungEc/)

DART(OpenDART)에서 삼성전기(009150)의 사업보고서·반기보고서·분기보고서를 수집하고, 재무지표를 계산해 GitHub Pages 대시보드로 표시하는 프로젝트입니다.

> **중요:** 이 ZIP은 저장소에 업로드할 프로젝트 파일입니다. 이 환경에서는 GitHub 계정에 로그인하거나 저장소 설정을 변경할 수 없으므로, 실제 push / Pages 배포 / About 링크 설정은 저장소 소유자가 아래 절차로 완료해야 합니다. 실제 수집 데이터는 `DART_API_KEY`를 등록한 뒤 GitHub Actions를 실행해야 생성됩니다.

## 빠른 설치
1. ZIP 압축을 풀고 파일을 저장소 `HSC-Class02/SC_SamsungEc` 루트에 업로드합니다. `.github/workflows` 폴더도 포함되어 있습니다.
2. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret** 에 `DART_API_KEY`를 만들고 OpenDART 인증키를 값으로 입력합니다.
3. **Settings → Pages → Build and deployment** 에서 Source를 **GitHub Actions**로 선택합니다.
4. **Actions** 탭에서 `DART financial data update` → **Run workflow** 를 실행합니다.
5. 배포 완료 후 `https://HSC-Class02.github.io/SC_SamsungEc/` 를 확인합니다. 저장소가 조직 정책상 Pages를 허용하는지 확인하세요.

## 자동 업데이트
워크플로는 매월 1일 00:20 UTC(한국시간 09:20)에 실행되며, Actions 탭에서 수동 실행도 가능합니다. GitHub 예약 실행은 부하 상황에 따라 지연될 수 있습니다. 데이터는 2010년부터 조회하도록 설정했습니다.

## 수집 데이터 및 주의
- 대상: 삼성전기, DART 고유번호는 실행 시 `company.json`에 설정한 `corp_code`를 사용합니다.
- 보고서: 사업보고서(11011), 반기보고서(11012), 1분기보고서(11013), 3분기보고서(11014)
- OpenDART API: 회사별 전체 재무제표 API를 사용합니다.
- API가 제공하는 계정명은 공시별로 다를 수 있으므로, `src/metrics.py`는 한글/영문 계정명 별칭으로 대표 항목을 매핑합니다. 값이 없으면 임의로 만들지 않고 빈 값으로 남깁니다.
- 분기·반기 손익은 API 응답 특성상 누적값인 경우가 있어, 분기 단독값으로 변환 가능한 경우에만 계산합니다. 원천 응답과 기간 유형을 `data/raw/` 및 데이터 파일에서 확인하세요.
- 본 프로젝트의 비율은 공시 숫자를 이용한 참고용 계산이며 투자 조언이 아닙니다.

## 재무지표
재무상태: 자산총계, 부채총계, 자본총계, 유동자산, 유동부채, 현금및현금성자산
손익: 매출액, 영업이익, 당기순이익
비율: 매출성장률, 영업이익률, 순이익률, 부채비율, 유동비율, ROA, ROE
(첨부 재무항목 목록을 확인할 수 없어 우선 표준 핵심지표를 기본값으로 구성했습니다. 추가 항목은 `config/metrics.json`에서 조정할 수 있습니다.)

## 국내 peer firms
아래 기업은 전자부품·MLCC·기판·카메라모듈 등 사업 중첩을 기준으로 한 **비교 후보**이며, 사업 포트폴리오가 완전히 같다는 뜻은 아닙니다.
- LG이노텍 (011070)
- 대덕전자 (353200)
- 심텍 (222800)
- 코리아써키트 (007810)
- 이수페타시스 (007660)

## 파일 구조
- `src/collect.py`: DART API 수집
- `src/metrics.py`: 핵심 계정 추출 및 비율 계산
- `src/build_site.py`: 정적 대시보드용 JSON 생성
- `dashboard/`: GitHub Pages 대시보드
- `.github/workflows/update.yml`: 매월 자동 실행 및 Pages 배포

## API 키 보안
API 키를 코드나 JSON 파일에 넣지 마세요. GitHub Actions Secret `DART_API_KEY`에만 저장하세요. 키를 공개 저장소에 커밋했다면 즉시 OpenDART에서 폐기/재발급하세요.
