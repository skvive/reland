# 강실장 블로그 · RE:LAND v3.0 연동 및 Google Blogger 개설 안내

## 로컬 실행

압축을 해제하고 `run_local.bat` 실행. Python 3.11 이상 필요. 주소:

- RE:LAND 본체: `http://127.0.0.1:8000/`
- 강실장 블로그: `http://127.0.0.1:8000/kang/`
- API: `http://127.0.0.1:8000/api/kang/metadata`, `/api/kang/lectures`, `/api/kang/qa`
- 강의 그림: `/kang/assets/lecture-001.svg` ~ `lecture-060.svg`
- 강의 슬라이드: `/kang/slides/lesson-001.html` ~ `lesson-060.html`
- 60개 블로그 개별 원고: `kang_blog/lectures/lesson-001.html` ~ 060.html
- 30개 Q&A 개별 원고: `kang_blog/qa/qa-001.html` ~ 030.html

## 실제 Blogger 개설 및 운영

1. 관리자가 본인 Google 계정으로 <https://www.blogger.com/>에서 신규 블로그 개설. **ZIP 제작 시점에는 개설하지 않음.**
2. 블로그 이름은 `재개발 강실장 | 알기 쉬운 재개발 법률상식`을 권장. 실제 주소 확정 전에 중복/사용 가능 여부 확인.
3. `kang_blog/index.html`는 시안용 **독립 웹앱**이며 Blogger용 업로드 검증을 거친 XML 테마가 아닙니다. Blogger 실제 테마는 `blog.css`·콘텐츠·헤더를 참고하여 템플릿 위젯으로 옮겨 구현해야 함.
4. 직접 블로그 글쓰기 화면에서 `kang_blog/lectures/*.html`, `kang_blog/qa/*.html` 원고를 복사·붙여넣은 뒤 이미지와 공식 링크를 확인하고 **비공개 초안으로 저장**.
5. 자동 비공개 초안을 원하는 경우 Google Cloud에서 OAuth 데스크톱 클라이언트를 생성하고 제공한 `scripts/publish_kang_blogger.py`를 사용. 본 도구는 공개 발행 기능 없음.

### Blogger 게시 사전검토 (외부 통신 없음)

```bash
python scripts/publish_kang_blogger.py --kind lecture --start 1 --count 3
python scripts/publish_kang_blogger.py --kind qa --start 1 --count 3
```

### 관리자 본인 계정으로 비공개 초안 만들기 (실제 외부 요청)

```bash
pip install -r scripts/requirements-blogger.txt
python scripts/publish_kang_blogger.py --kind lecture --start 1 --count 3 --blog-id BLOG_ID --client-secret "C:/private/oauth-client.json" --confirm
```

**주의:** 이 도구는 Blogger 블로그 생성이 아닌 **기존 블로그의 비공개 게시물 초안 추가**만 합니다. `--confirm` 없이 호출하면 API나 Google 계정에 아무것도 보내지 않습니다. OAuth JSON은 ZIP/깃허브에 넣지 않습니다.

## 보안·개인정보

- 공개 연락처는 운영자가 지정한 이메일 한 개입니다. 추가 전화번호·성명·개별 사건 접수 폼을 만들지 않았습니다.
- HTML에는 변호사 자격·박사 학위·로펌 경력을 증빙 완료 사실처럼 표시하지 않았습니다.
- PWA·쿠키 등 RE:LAND 본체의 환경설정/보안 한계는 프로젝트 `README.md`를 확인하십시오.
- 60강·30문답은 현재 `noindex` 미리보기 상태입니다. **법률 감수와 서버 보안·개인정보 검토 전에는 검색엔진에 권위 있는 법률 자문처럼 노출하지 마세요.**

## 도식과 AI 이미지

- 60개 SVG는 프로그램으로 제작한 **교육용 개념도**. 정확한 사업구역 경계나 건축 설계도를 의미하지 않습니다.
- 캐릭터와 주제별 실사 이미지는 AI 제작. 실제 인물 사진/특정 사업장의 확정 조감도가 아닙니다.
- 원본 참고 사진 파일을 ZIP에 포함하지 않았습니다.
