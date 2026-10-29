# 최종 QA 검사 요약

검사일: 2026-10-29

- Python API 테스트: **19/19 통과** (`docs/TEST_RESULTS.txt` 참조)
- Node JavaScript 구문 검사: 통과 (`node --check static/app.js`)
- Python 컴파일 검사: 통과 (`python -m compileall app.py scripts`)
- Headless Chromium DOM 검사: **홈·지도·커뮤니티 생성·모임 가입 안내·신규 게시글 작성·댓글 추가·전문가 상담 폼** 작동 확인
- 모바일 390×844 검사: `document.documentElement.scrollWidth === window.innerWidth`(390px), 페이지 전체 가로 넘침 없음
- 브라우저 JS 런타임 예외: 검사 동안 0건
- 지도 폴백: Leaflet/OSM 타일 네트워크 접근 없이 지역 목록 17개와 도식 핀 정상 표시
- 홈·지도·전문가·모바일 화면 캡처: `docs/*.png` 포함

**제약:** 검사 컨테이너의 Chromium 정책이 웹 URL 직접 탐색을 차단하여, DOM 테스트는 HTML/CSS/JS를 브라우저에 주입하고 서버 API를 실제 FastAPI TestClient로 연결하는 방식으로 수행했습니다. 운영 도메인 기반 HTTP 탐색과 실제 Google SSO, 외부 RSS, 정확한 지리 경계 연동 및 전문가 매칭은 별도 운영 환경에서 재검증해야 합니다.

**ZIP 정리:** 테스트 시 생성된 데모 사용자, 글, 상담 및 지역 데이터가 담긴 `data/reland.sqlite`는 배송 ZIP에서 제거합니다. 서버 첫 실행 시 시연 데이터가 새로 생성됩니다.
