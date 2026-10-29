# 관리자 RE:LAND Google Blogger 개설 및 비공개 초안 발행

**중요: 이번 코드 패키지는 사용자 Google 계정의 블로그를 직접 개설하지 않았고 외부 Blogger 게시도 실행하지 않았습니다.** Google Blogger API v3는 Blogs.insert가 없으며, 이미 소유한 블로그의 `Posts.insert`만 지원합니다.

## 직접 개설할 때

1. 구글 관리자 본인이 https://www.blogger.com/ 으로 접속하여 별도 관리 계정으로 로그인합니다.
2. 새 블로그 개설 메뉴에서 예: `RE:LAND 재개발 법률 저널`이라는 제목과 사용 가능한 주소를 선택합니다. **주소는 제안일 뿐 실제로 예약되지 않았습니다.**
3. 게시 설정과 개인정보·광고·댓글 모더레이션 정책을 설정합니다.
4. Google Cloud에서 Blogger API v3 활성화 및 데스크톱 앱 OAuth 클라이언트 JSON을 발급합니다. 이 JSON은 비밀정보이므로 ZIP에 넣거나 Git에 커밋하지 않습니다.
5. Blogger 관리화면에서 자신의 블로그 ID를 확인합니다. 도메인 주소만으로 게시 API를 호출할 수 없습니다.
6. 아래 예제로 연결합니다. 발행 전 120개 원고의 사실관계·조문 시행일·이미지·오탈자·중복문구를 분야별 전문가가 개별 검토해야 합니다.

## 로컬 사전 검수

```bash
python scripts/publish_blogger.py --start 1 --count 5
```

이 명령은 API에 접근하지 않으며 다섯 편의 원고 제목만 인쇄합니다.

## 승인 후 비공개 Blogger 초안 생성

```bash
python -m pip install -r scripts/requirements-blogger.txt
python scripts/publish_blogger.py --blog-id "본인블로그ID" --client-secret "C:/safe/oauth_client.json" --start 1 --count 5 --confirm
```

- `--confirm`을 사용해도 공개 발행하지 않고 `isDraft=true`로 Blogger에 **비공개 초안만 생성**합니다.
- 한 번에 최대 10편까지만 전송하도록 제한했습니다. 실패 시 완료한 글의 ID가 `data/blogger_draft_receipts_<blogid>.json`에 남아 재시도 시 중복 생성을 방지합니다.
- 실제 공개 배포된 이미지가 있다면 `--image-base-url https://your-domain.example/static`을 추가합니다. 없으면 본문 이미지를 삽입하지 않습니다.
- 미리 생성한 HTML 초안은 `blogger_drafts/column-001.html`부터 `column-120.html`까지 개별 저장되어 있습니다.
- OAuth 인증 진행 시 구글 계정 비밀번호를 코드나 채팅에 입력하지 않습니다.

## Google / YouTube 정책

- Blogger 공식 API 문서: https://developers.google.com/blogger/docs/3.0/reference/posts/insert
- Blogs API 기능 목록: https://developers.google.com/blogger/docs/3.0/getting_started
- YouTube 영상 큐레이션은 관리자가 검수·승인한 실제 URL만 저장하고 기본 YouTube iframe을 사용합니다. 가짜 조회수나 저작권 미확인 영상은 금지합니다.
- 출처 링크: https://developers.google.com/youtube/terms/developer-policies-guide
