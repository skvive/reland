## Learned User Preferences

- LEXID·RE:LAND 등 에디토리얼·실사 썸네일은 OpenAI `gpt-image`/Bailian 일괄 생성 대신 Cursor 네이티브 `GenerateImage`만 사용한다(사용자 명시: 「커서이미지 생성으로해」).

## Learned Workspace Facts

- Cursor 워크스페이스 `E:\currsor_C\blog`는 LEXID ZIP 핸드오프 추출·분석(`_import`, `_extract_lexid`, 제품별 하위 폴더)과 `goobl/` 서브트리를 담는 허브이다.
- 신규 LEXID 사이트는 보통 `C:\cursor\<product>`에 구현하고 `skvive/<product>` 리포에 푸시한 뒤 Vercel `*.lexid.site`와 Neon Postgres로 배포한다.
- 동일 패턴으로 진행된 제품 예: `skvive/meta`(meta.lexid.site), `skvive/medipick`, `skvive/garakland`, `skvive/lawygototal`(LAWYGO 마스터 ZIP 기준 멀티 도메인).
- RE:LAND 배포 소스는 `E:\currsor_C\blog\reland-deploy`(GitHub `skvive/reland`), 프로덕션 URL `https://reland.lexid.site`(레거시 별칭 `rerand.lexid.site` 가능).
- RE:LAND 칼럼(120)·「재개발 강실장」강의(60) 썸네일 파이프라인: Cursor `GenerateImage` → `C:\Users\user\.cursor\projects\e-currsor-C-blog\assets` → `scripts/ingest_cursor_assets.py` → `static/assets/columns/`·`kang_blog/assets/lessons/` WebP(검증: `scripts/verify_cursor_images.py`).
