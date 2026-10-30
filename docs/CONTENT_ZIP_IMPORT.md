# RE:LAND 콘텐츠 ZIP 이식 (v3.0.2 / Premium v4.1)

## ZIP 경로 (Dropbox)

- `RELAND_v3.0.2_교육콘텐츠210_AI이미지210_게시판통합_QA완료.zip`
- `RELAND_Premium_Design_v4.1_원본종_반영8페이지_디자인팩키지.zip`

로컬에 ZIP이 없으면 Dropbox에서 동기화한 뒤 아래 명령에 **전체 경로**를 넣습니다.

## v3.0.2 — JSON·이미지·게시판

| 패키지 구역 | 사이트 반영 |
|------------|------------|
| `content/columns_120.json` | `/columns` · Legal Studio |
| `content/kang/*.json` | `/api/kang/*` · `/kang/` |
| AI 이미지 `columns/` · `lessons/` | `static/assets/columns/` · `kang_blog/assets/lessons/` |
| 게시판 통합 (210건) | 커뮤니티 3곳 + 게시글 210 (`content_publisher.py`) |

### 게시판 매핑

1. **RE:LAND 법률지식** — 칼럼 120 → `discussion`, 링크 `/column/{id}`
2. **재개발 강실장 클래스** — 강의 60 → `discussion`, 링크 `/kang/lectures/lesson-NNN.html`
3. **강실장 Q&A TOP30** — Q&A 30 → `question`, `resolved=1`

시드 키: `posts.seed_key` / `communities.seed_key` (중복 삽입 방지).  
버전 마커: `settings.content_boards_seed` = `v3.0.2-210-boards`.

```powershell
cd E:\currsor_C\blog\reland-deploy
python scripts/import_reland_zip.py `
  --v302 "C:\Users\user\Dropbox\PC (9)\Downloads\RELAND_v3.0.2_....zip" `
  --apply-boards
```

이미 JSON만 반영된 상태에서 게시판만 넣을 때:

```powershell
python scripts/seed_content_boards.py
python scripts/seed_content_boards.py --force
```

프로덕션(Neon): `DATABASE_URL` 설정 후 동일 스크립트 1회 실행.

## v4.1 — 디자인 8페이지

```powershell
python scripts/import_reland_zip.py `
  --design "...\RELAND_Premium_Design_v4.1_....zip"
```

에셋은 `static/premium_v41/` 로 복사됩니다. SPA에 단계적으로 반영 시 `docs/DESIGN_QA.md`·`docs/BRAND_SYSTEM.md` 기준으로 연결합니다.
