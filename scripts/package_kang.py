"""Regenerates in-browser DATA object and standalone Blogger HTML theme sample."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'kang_blog';C=ROOT/'content'/'kang'
data={'lectures':json.loads((C/'lectures_60.json').read_text()),'qa':json.loads((C/'qa_30.json').read_text()),'sources':json.loads((C/'sources.json').read_text())}
(K/'data.js').write_text('window.KANG_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n',encoding='utf-8')
# Export the blog design for preview/hosting. Blogger themes are XML with widget rules; this is intentionally a CSS+layout candidate.
(K/'BLOGGER_THEME_GUIDE.txt').write_text('''Blogger 맞춤형 테마 적용 참고\n\n1. 실제 Google 계정으로 https://www.blogger.com/ 에서 새 블로그를 만들고 원하는 블로그 이름과 주소를 지정합니다. (이 ZIP은 계정/블로그를 대신 개설하지 않았습니다.)\n2. 본 ZIP의 kang_blog/index.html, blog.css, assets/ 는 자체 호스팅 시안입니다. Blogger의 XML 테마 파일로 그대로 업로드할 수 있다고 주장하지 않습니다.\n3. Blogger에서 테마 > HTML 편집에 맞는 b:section / b:widget 구조로 변환하고 테스트 블로그에서 검수하세요. 배너·프로필 이미지는 Blogger 미디어나 별도 HTTPS 공개 호스팅에 먼저 업로드하십시오.\n4. 개별 강의 HTML은 kang_blog/lectures/, Q&A HTML은 kang_blog/qa/ 입니다. 법률 전문가 검수와 링크 검증 후 블로그 관리자 화면에 복사해 비공개 초안으로 등록하세요.\n5. 기존 블로그 ID/OAuth를 보유하면 scripts/publish_kang_blogger.py의 기본 미리보기 모드로 점검하고 명시적 --confirm을 주어 비공개 초안 생성이 가능합니다. 자동 공개 발행은 구현하지 않습니다.\n6. 공개 작성자 표시는 ‘재개발 강실장 · 교육 콘텐츠 에디터’이고, 변호사 또는 박사학위자라는 표현을 사용하지 않습니다. 이메일은 교육 관련 문의 전용입니다.\n''',encoding='utf-8')
print('data.js', (K/'data.js').stat().st_size)
