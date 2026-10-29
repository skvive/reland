# RE:LAND v1.1 (리랜드) — 전국 정비사업 지도·SNS·법률 정보 웹앱

## 주요 기능

- 지도 중심 전국 17개 권역 **시연 허브** + 국토교통부 공식 1,566행 CSV를 가져오기 위한 도구
- 정비사업 목록, 유형·진행단계·지역 필터, 각 구역 상세 정보·법령 출처 표시
- Google Identity Services 로그인(ID 토큰 RSA 서명·aud·iss·exp 검증, HttpOnly 세션)
- 비공식 주민모임 생성·팔로우, 질문·게시글·댓글·좋아요·북마크·신고
- 조합 관련 인증 요청 접수(승인 전 법적 조합원·공식 조합 표기 없음)
- Google Blogger 프로필 링크 등록 및 공개 RSS 미리보기(소유권 인증 및 자동발행 아님)
- 도시정비법 절차·정책 정보, 뉴스 검색 RSS 제목·원문 링크 캐시
- 전문가 상담 **접수만** 제공. 실제 법무법인 연결·답변은 전문인력 및 별도 계약 필요
- 실사 도시 조감 이미지(생성형 AI), 반응형 디자인, 모바일 대응
- 개인정보 게시 최소화 안내, 관리자 신고 조회/숨김 API, SQLite 영속 저장
- **v1.1** 관심 정비구역 저장/해제, 공식 CSV 재반영 시 단계 변경 감지와 개인별 변경 내역
- **v1.1** 서울 등 지자체 공개 도형을 별도 검증해 업로드하는 WGS84 GeoJSON 폴리곤 레이어
- **v1.1** 내 활동 대시보드(상담 처리상태·관심 구역·단계 변경·게임형 참여점수·배지)
- **v1.1** 운영자의 상담 처리상태 수정 및 변경 감사 기록, 파일 기반 환경변수 설정

## 빠른 실행

### Windows

1. Python 3.11 이상 설치 (환경 변수 PATH 등록).
2. 압축 해제 후 `run_local.bat` 실행. 첫 실행은 PyPI 설치를 위해 인터넷 연결 필요.
   처음 실행하면 `.env.example`을 복사해 `.env` 설정파일을 자동 생성합니다.
3. 자동으로 브라우저가 열리지 않으면 `http://127.0.0.1:8000`을 입력.
4. Google OAuth 설정 전에는 **로컬 체험 로그인**으로 커뮤니티 기능을 테스트할 수 있습니다.

### macOS / Linux

```bash
python -m pip install -r requirements.txt
python app.py
```

### 테스트

```bash
python -m pip install pytest
python -m pytest -q tests
```

## 실제 공공데이터 가져오기

공공데이터포털에서 [국토교통부 전국 도시정비사업 통합 데이터](https://www.data.go.kr/data/15160169/fileData.do) (2026-05-18 기준) CSV를 다운로드합니다. 이 파일은 **시도, 시군구, 구역명, 현재 추진단계, 사업유형, 사업시행자, 공급 예정 세대 수**를 포함합니다. **좌표·정확한 구역 경계는 포함되지 않습니다.**

```bash
python scripts/import_districts.py "C:/Downloads/official.csv" --dry-run
python scripts/import_districts.py "C:/Downloads/official.csv"
```

진짜 정비사업 행은 `demo=0`으로 저장하고, 시연용 지역 허브는 `demo=1`로 분리합니다. 시·도 대표 위치는 `precision=province_center`로 명시하여 정확한 위치인 것처럼 표시하지 않습니다. 좌표가 검증된 지자체 고시 폴리곤은 `scripts/import_boundaries.py`로 **별도** 적재할 수 있습니다.

```bash
# 검증 전 미리보기(변경 없음)
python scripts/import_boundaries.py official-zone.geojson --source-url "https://agency.go.kr/source" --source-date 2026-10-29 --confirm-reviewed --dry-run
# 실제 등록: 작업자가 원본·이용권한·WGS84 좌표계를 확인한 경우만
python scripts/import_boundaries.py official-zone.geojson --source-url "https://agency.go.kr/source" --source-date 2026-10-29 --confirm-reviewed
```

`GeoJSON`의 각 Feature에 `properties.district_id` 또는 정확한 `name`, `province`, `city`를 포함합니다. 좌표계는 **EPSG:4326, [경도, 위도]**여야 합니다. 좌표 구조·한국 범위·DB 참조는 자동 검사하지만 **해당 경계가 법적으로 확정된 원본인지 여부는 자동 검사할 수 없습니다.** 정확한 폴리곤 원본이 없는 지역은 도식용 중심점만 사용합니다. `--confirm-reviewed`는 사람의 검토 완료 선언이며 원본 진위 판정이 아닙니다.

## Google 로그인 활성화

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials)에서 프로젝트와 **웹 애플리케이션 OAuth 클라이언트 ID**를 생성합니다.
2. Authorized JavaScript origins에 실제 배포 도메인(`https://your-domain.example`) 또는 개발 도메인(`http://localhost:8000`/`http://127.0.0.1:8000`)을 등록합니다.
3. `.env` 파일의 `GOOGLE_CLIENT_ID`에 발급된 **공개 클라이언트 ID**를 넣습니다. 운영 환경변수가 있으면 그 값을 우선 사용합니다. Secret은 브라우저에 포함하지 않습니다.
4. 서버를 재시작하고 Google 계정으로 로그인 버튼을 확인합니다.
5. 실제 서비스에서는 `ENVIRONMENT=production`, `RELAND_DEMO_MODE=0`, HTTPS 리버스프록시, 고유 `RELAND_ADMIN_KEY` 설정이 필수입니다.

**주의:** Google 로그인은 리랜드 계정 인증만 처리합니다. 조합원 자격·Blogger 소유권·법정 조합 지위 검증과는 무관합니다.

## 서버 배포

이 프로젝트는 Python FastAPI + SQLite + 정적 HTML/CSS/JS를 사용하며 npm 빌드가 필요 없습니다. 지속적 파일 저장 공간이 있는 Linux VPS나 PaaS에 다음 명령으로 배포할 수 있습니다.

```bash
ENVIRONMENT=production RELAND_DEMO_MODE=0 GOOGLE_CLIENT_ID='your-client-id' \
RELAND_ADMIN_KEY='a-long-random-secret' \
uvicorn app:app --host 127.0.0.1 --port 8000 --proxy-headers
```

Nginx/Caddy 등 **TLS 종료 프록시** 뒤에 서버를 두고 HTTPS를 적용하세요. SQLite 파일 `data/reland.sqlite`는 개인 데이터이므로 백업·암호화·접근권한을 설정하십시오. 멀티 인스턴스로 확장할 경우 PostgreSQL과 공유 세션 저장소, 중앙 집중 속도제한, 작업 큐로 교체해야 합니다.

정식 운영 전 `.env`의 예시 관리자 비밀키를 반드시 교체하고 데모 로그인을 꺼야 합니다. `RELAND_ADMIN_KEY`를 설정한 뒤 관리자는 서버 사이드에서 `GET /api/admin/reports` 및 `POST /api/admin/posts/{id}/hide`를 `X-Admin-Key` 헤더로 호출할 수 있습니다. 키를 일반 사용자 브라우저 JS에 넣지 마세요.

## 뉴스 갱신

서버가 Google 뉴스 검색 RSS를 캐시합니다. 최초 요청 시 갱신을 시도하며, 이후 3시간 간격으로 요청합니다. 기사 **제목·출처·날짜·원문 URL만** 보존합니다. 실서비스 운영 시 뉴스 제공처 약관 및 요청 빈도를 확인하세요.

매일 06:10 KST 갱신이 필요하면 Windows 작업 스케줄러 또는 Linux cron에 다음 명령을 등록하십시오.

```bash
python scripts/sync_news.py
```

공공 뉴스 RSS가 차단되거나 인터넷 연결이 없으면 빈 상태를 정상적으로 표시합니다. 새 뉴스 또는 자동 크롤링 성공을 허위로 주장하지 않습니다.

## 제공 범위 / 아직 미구현된 영역

| 기능 | 이번 ZIP의 상태 |
| --- | --- |
| 전국 지도, 지역 검색, 필터 | 실행 가능. 실제 원본은 사용자가 CSV 내려받아 가져오기 |
| 3D 게임형 GIS | 시각적 분위기·실사 도시 이미지 제공. 3D 공간 데이터 렌더링 미구현 |
| Google 계정 로그인 | ID 검증 구현. 운영 OAuth 클라이언트 ID 필요 |
| 조합원 인증·공식 조합 마크 | 요청 접수만. 수동 심사·법적 조직 확인 프로세스 필요 |
| SNS / 댓글 / 좋아요 / 팔로우 / 신고 | DB에 저장되는 기능 구현 |
| Google Blogger 연동 | 프로필 링크·공개 RSS 미리보기. 계정 OAuth·자동 게시 불가 |
| 뉴스 자동 업데이트 | 공개 RSS 조회/저장 코드 구현. 실제 네트워크 연결에 의존 |
| 전문가 상담 | 접수 DB 및 선택적 운영자 메일 통지. 전문가 배정 불가 |
| 개인정보 보호·법률 검토 | 기본 보호조치 및 가이드 제공. 운영 전 전문 법률 검토 필요 |

추가 설계·보안·품질·법률 리스크는 `docs/CRITICAL_REVIEW.md`를 참고하세요.

## 앱 설치형(PWA) 지원

`manifest.webmanifest`와 `sw.js`가 포함되어 있습니다. 운영 HTTPS 도메인에서는 브라우저의 **홈 화면에 추가/앱 설치** 기능을 사용할 수 있습니다. 정적 앱 셸만 캐시하고, 개인정보·상담·게시글 API 응답은 오프라인 캐싱하지 않습니다.

## 운영자 조합 확인·질문 게시판 추가 기능

- 질문 작성자 답변 완료 토글 / 본인 글 숨김 삭제 / 회원 탈퇴 시 글 익명화 및 관심 구역 해제
- 독립 증빙 검증 후 관리자 전용 API로 조합 관련 확인 요청 심사, 커뮤니티 공식 표시, 감사 기록
- 운영자 콘솔 UI 및 정부기관 연계 검증은 후속 개발사항

**검증문서:** `docs/CRITICAL_REVIEW.md`, `docs/PROJECT_STRUCTURE.md`를 확인하세요.

### 커뮤니티별 Blogger 공개 글

각 커뮤니티를 만든 운영자는 모임 상세 페이지에서 공개 `https://블로그명.blogspot.com/` 링크를 연결할 수 있습니다. 공개 RSS 게시물 제목 및 원문 링크를 모임에서 미리 볼 수 있습니다. **Google OAuth Blogger 발행 권한은 사용하지 않으며 블로그 소유권을 증명하는 기능도 아닙니다.**

## v1.1 개인 맞춤 기능 · 운영 API

- `POST /api/districts/{id}/watch` : 공식 구역 관심 등록·해제(로컬 데모 허브는 금지)
- `GET /api/my/dashboard` : 관심 구역·원본 변경 이력·내 상담 처리상태·참여 배지(로그인 필요)
- `GET /api/map/boundaries` : 검증 후 수동 등록한 폴리곤 데이터만 지도 표시
- `GET /api/districts/{id}/geometry` : 상세 구역 경계 도형·원본 링크 확인
- `POST /api/admin/consultations/{id}/status` : 관리자만 상담 상태를 접수/검토중/연락완료/종료로 변경, 감사 로그 저장

사용자에게 지급되는 커뮤니티 참여점수·배지는 **비거래형 게임 요소**로, 법률·투자 신뢰도·조합원 자격과 무관합니다. 개인정보를 포함한 지도 즐겨찾기와 변경 이력은 해당 로그인 회원에게만 공개됩니다.

## 검수 · 재현

```bash
python -m pip install pytest
python -m pytest -q tests     # 30개 자동 테스트
node --check static/app.js    # Node.js가 설치된 경우 프런트엔드 문법 검사
python -m py_compile app.py scripts/*.py
```

브라우저 UI 검수는 외부 네트워크와 로컬 웹주소가 차단된 환경에서 별도의 HTML/CSS/JS 주입+FastAPI TestClient 브리지로 수행했습니다. 재현하려면 추가로 `pip install playwright` 및 Chromium 브라우저가 필요하며, `CHROMIUM_PATH`(또는 Playwright가 내려받은 기본 Chromium)를 설정해 `python tests/ui_smoke.py`를 실행하세요. **이 방식은 실제 서비스 호스팅, Google SSO, OSM 타일, 언론사 RSS, SMTP 연결에 대한 운영 E2E 테스트를 대체하지 않습니다.** 검수 캡처는 `docs/v11-*.png`에 보관했습니다.

## RE:LAND v2.0 — 법률 저널·전문가 네트워크·Blogger 발행 도구

기존 v1.1 기능은 유지하고, 다음을 추가했습니다.

- `/columns` — **120편 법률 전문 편집 원고** 목록·카테고리·검색·페이지네이션. 모두 출처 조문 발췌 및 법제처 전체 원문 링크 제공. **법률 전문가 감수 미완료** 명시.
- `/column/1` … `/column/120` — 120개 개별 상세 페이지. 법률 적용 범위·문서 체크리스트·법조문 원문 링크·AI 설명 이미지 제공.
- `/directory` — 변호사·법무사·행정사 **실제 전문가가 입점 신청**하여 관리자 수동 검토 후에만 공개되는 디렉터리. 검색·지역·직역 필터.
- `/expert/{id}` — 직접 연락처, HTTPS 사이트, Blogger, YouTube 채널, 승인된 칼럼.
- `/shorts` — 관리자가 실제 원본 영상을 검토하고 등록하는 YouTube 큐레이션. 초기 실제 영상 0개이며 가짜 데이터를 사용하지 않음.
- 전문가가 입점 신청, 기사 원고 제출, 운영자 승인 심사, 유료 광고 공개 라벨 및 익명 비과금 활동 집계.
- `content/columns_120.json` / `content/law_references.json` / `content/columns_manifest.csv` — 콘텐츠 원본과 인용자료.
- `blogger_drafts/` — **120개 Blogger 발행용 HTML 원고 초안**.
- `scripts/publish_blogger.py` — 기존 Blogger 블로그에 OAuth 허용 후 **비공개 초안 게시**. 실제 외부 블로그 생성/게시 전혀 미실행.
- `scripts/studio_admin.py` — 로컬 환경변수로 보호하는 운영자용 검수·등록·통계 명령.
- `docs/BLOGGER_SETUP.md`, `docs/LAW_EDITORIAL_SAFETY.md` — 외부 서비스 연결 및 법률상 주의사항.

### 검증 명령

```bash
python scripts/build_editorial.py
python -m pytest -q tests
python -m py_compile app.py legal_studio.py scripts/*.py
node --check static/app.js
```

실제 Google Blogger 블로그/뉴스/YouTube 인증/외부 광고 계약은 사용자의 명시적 권한과 설정이 있어야 하므로 코드만으로 완료되지 않습니다.

---

# RE:LAND v3.0 — 「재개발 강실장」 교육·법률 블로그 통합 패키지 (2026-10-29)

기존 v2.0 앱의 120편 **별도 미감수 편집 원고**와 지도·SNS·전문가 기능은 유지하면서, **재개발 강실장** 독립 교육 저널을 `/kang/` 경로에 연동했습니다.

### 이번에 새로 제작한 콘텐츠 및 기능

- **60편** 분야별 재개발 법률 강의: 분담금·감정평가 / 조합 갈등·총회 / 행정절차·정보공개 / 행정심판 / 행정소송 / 민사소송의 구조 / 형사고소 절차 / 인허가·도면 / 분양·관리처분 / 보상·이주·갈등관리 (10개 분야, 분야별 6강)
- **30개** 구역·법률 절차에 관한 FAQ. 각 답변은 해당 국가법령정보센터 공식 조문에 연결.
- **60개** 교육용 SVG 절차 개념도, **60개** 화면 강의 슬라이드 HTML, **12개** AI 주제 콘셉트 이미지, **1개** 사용자 사진 기반 애니메이션 캐릭터 (원본 실사진 비포함)
- **90개** Blogger 복사용 개별 HTML 강의/문답 초안. 로컬 서버 내 공개용 시안 사이트, 카테고리 필터·검색·문답 펼치기·상세 팝업과 공식 원문 링크.
- `scripts/publish_kang_blogger.py` — 관리자 OAuth 승인 후 **비공개 초안만** 발행하도록 설계. 기본 모드는 외부통신 **0건**.
- `api/kang/metadata`, `api/kang/lectures`, `api/kang/qa` — RE:LAND 통합 API. 메뉴에 강실장 블로그 연결.
- **공개 담당자**: `재개발 강실장 · 교육 콘텐츠 에디터` / 이메일 `kangjunchul8@gmail.com`만 노출. 원본 사진, 실명, 법률사건 수임 프로필, 변호사 또는 박사 자격 주장은 사용하지 않습니다.

### 로컬 확인 URL

- `http://127.0.0.1:8000/` — RE:LAND 본체
- `http://127.0.0.1:8000/kang/` — 강실장 블로그 디자인
- `http://127.0.0.1:8000/kang/slides/lesson-001.html` — 강의 슬라이드 1강
- `http://127.0.0.1:8000/api/kang/lectures` — 강의 원고 API

### 법적·운영상 한계 (반드시 확인)

**60강·30문답은 법조문·판례 링크를 확인해 만든 교육 편집 초안이며, 개별 법률전문가가 90편 모두를 검수한 완성 법률의견서는 아닙니다.** 실제 사건별 법률상담, 대리, 유상 소장/고소장 작성 기능은 없습니다. 변호사법 제34조 및 제109조를 참고하세요. 공개 전 주제별 판례, 시행법령, 관련 조례, 개인정보 검수를 실시해야 합니다.

**관리자 Google 블로그는 실제 개설하지 않았고**, 블로그에 어떠한 글도 실게시하지 않았습니다. `kang_blog/index.html`는 Blogger XML 테마 설치 검증 완료본이 아닌 **독립 웹앱 디자인 시안**입니다. Google Blogger 사이트에서 실제 블로그를 개설하고 테마 위젯 변환·사진 업로드·OAuth를 설정해야 비공개 초안을 올릴 수 있습니다.

상세: `docs/kang/CONTENT_INDEX.md`, `docs/kang/EDITORIAL_POLICY.md`, `docs/kang/INTEGRATION_AND_BLOGGER.md`, `kang_blog/BLOGGER_THEME_GUIDE.txt`.

### 재생성 및 검사

```bash
python scripts/build_kang.py
python scripts/package_kang.py
python -m pytest -q tests
python tests/ui_kang.py      # Chromium + playwright 필요; 외부 네트워크가 아닌 주입 기반 화면 검사
node --check kang_blog/blog.js
```

편집 스크립트를 재실행하면 강의·Q&A 초안과 도식을 재생성합니다. 실제 법률 감수 이후 원고를 수정했다면 기존 파일을 먼저 백업하십시오.
