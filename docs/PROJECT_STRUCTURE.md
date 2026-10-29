# 파일 구조 및 주요 API

```text
reland-platform/
├── app.py                  FastAPI 서버, SQLite, 인증, SNS, 뉴스, 상담
├── static/
│   ├── index.html          페이지 골격, SEO 기본 메타
│   ├── style.css           반응형 UI 스타일
│   ├── app.js              라우터, 지도, 페이지, SNS UI
│   ├── manifest.webmanifest PWA 매니페스트
│   ├── sw.js               공개 정적 파일만 캐싱하는 서비스 워커
│   └── assets/             AI 조감 이미지·앱 로고
├── scripts/
│   ├── import_districts.py 국토부 공식 CSV 유효성 검증·DB upsert
│   └── sync_news.py        뉴스 제목·링크만 갱신
├── tests/test_api.py       18개 API/권한/데이터 단위 테스트
├── docs/                   검토문서와 화면 검수 캡처
├── data/                   실행 시 생성되는 SQLite 파일 경로
├── requirements.txt        Python 필수 패키지
├── .env.example            설정 예시 (자동 로드하지 않음)
├── run_local.bat           Windows 원클릭 로컬 실행
└── run_local.sh            Linux/macOS 로컬 실행
```

## 읽기 API

- `GET /api/health`
- `GET /api/config`
- `GET /api/stats`
- `GET /api/districts?q=&region=&kind=&stage=&limit=`
- `GET /api/districts/{id}`
- `GET /api/communities`
- `GET /api/communities/{id}`
- `GET /api/posts?community_id=&kind=&q=&limit=`
- `GET /api/posts/{id}`
- `GET /api/news?topic=&limit=`
- `GET /api/blog/preview?url=https%3A%2F%2Fexample.blogspot.com%2F`
- `GET /api/auth/me`

## 로그인·쓰기 API

- `POST /api/auth/google` `{ "credential": "google-jwt" }`
- `POST /api/auth/demo` **로컬 시연에서만**
- `POST /api/auth/logout`
- `PUT /api/auth/profile` 닉네임·자기소개·공개 Blogger 주소
- `DELETE /api/auth/account` `{ "confirmation": "DELETE MY ACCOUNT" }`
- `POST /api/communities` 새 비공식 모임
- `POST /api/communities/{id}/follow` 팔로우 토글
- `POST /api/communities/{id}/verification` 확인 요청
- `POST /api/posts` 게시글·질문 작성
- `POST /api/posts/{id}/comments` 댓글
- `POST /api/posts/{id}/like` 좋아요 토글
- `POST /api/posts/{id}/bookmark` 저장 토글
- `POST /api/posts/{id}/report` 신고
- `POST /api/posts/{id}/resolve` 질문 작성자 답변 완료
- `DELETE /api/posts/{id}` 본인 글 숨김 처리
- `POST /api/consultations` 동의 기반 상담 접수

## 운영자 API

모든 호출에 `X-Admin-Key: <RELAND_ADMIN_KEY>` 헤더가 필요합니다.

- `GET /api/admin/reports` 신고·인증·상담 대기 목록
- `POST /api/admin/posts/{id}/hide` 신고된 글 숨김
- `POST /api/admin/verification/{id}/review` `{ "approved": true, "note": "검토 근거 10자 이상" }`
- `POST /api/admin/communities/{id}/official` `{ "approved": true, "note": "검토 근거 10자 이상" }`

검토 없이 공식조합 인증을 부여하면 안 됩니다. 이 API는 운영자 수기 확인 프로세스의 일부이며 실제 법적 인증 플랫폼이 아닙니다.


## v1.1 files
- `scripts/import_boundaries.py` — operator-only curated GeoJSON polygons
- `tests/test_v11.py` — district watches, geometry source checks, stage changes, admin status
- `tests/ui_smoke.py` — optional injected Chromium test harness
- `docs/v11-{home,map,profile,mobile}-browser.png` — screen captures


## v2.0 modules

- `legal_studio.py`: FastAPI studio router; SQLite migration on DB init; experts, ads, metrics, videos, article retrieval.
- `content/columns_120.json`: 120 substantive *editorial review* drafts, not 120 independently legal-reviewed published columns.
- `content/law_references.json`: 9 original law excerpts with official law.go.kr links.
- `blogger_drafts/`: 120 HTML drafts for manual Blogger import. Images need external hosting or manual replacement.
- `scripts/build_editorial.py`: deterministic editorial generator / cropped AI concept derivatives.
- `scripts/publish_blogger.py`: opt-in OAuth, non-public Blogger draft-only API.
- `scripts/studio_admin.py`: administrator CLI using server secret in environment.
- `/columns` `/column/{id}` `/directory` `/expert/{id}` `/shorts` `/partners`: v2 UI screens.
- `tests/test_studio.py` + `tests/admin_integration_check.py`: new integration tests.

## Warning: no invented specialist people

Initial expert directory intentionally has no specialist records. All displayed experts require opt-in admission and manual verification; tests only create fictitious temporary users in test databases and are not shipped as live profiles.
