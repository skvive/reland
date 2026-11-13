'use strict';
(() => {
  const DATA = window.KANG_DATA;
  const params = new URLSearchParams(location.search);
  const id = Number(params.get('id'));
  const lecture = DATA && DATA.lectures && DATA.lectures.find(x => x.id === id);
  const $ = sel => document.querySelector(sel);
  const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  if (!lecture) { $('#lectureTitle').textContent = '강의를 찾을 수 없습니다'; $('#lectureSummary').textContent = '강의 목록에서 다시 선택해주세요.'; return; }
  // Official approved-brand image stays constant. Each lecture's own AI scene is placed below.
  const brandImage = $('#lectureImage');
  brandImage.dataset.brandHero = '1';
  brandImage.removeAttribute('data-lesson-media-id');
  brandImage.loading = 'eager';
  brandImage.decoding = 'async';
  brandImage.src = '/kang/assets/kang-class-hero-v5.webp';
  brandImage.alt = 'RE:LAND 강실장 클래스 공식 승인 브랜드 이미지';
  $('#lectureEyebrow').textContent = `RE:LAND · KANG CLASS / LECTURE ${String(id).padStart(2, '0')}`;
  $('#lectureTitle').textContent = '강실장 클래스';
  $('#lectureSummary').textContent = '재개발·재건축 실전 지식을 이야기로 배웁니다';
  const sceneImage = $('#storySceneImage');
  const scenePath = window.KANG_MEDIA_V16?.get(id) || `/kang/assets/lessons/lesson-${String(id).padStart(3,'0')}.webp`;
  sceneImage.dataset.lessonMediaId = String(id);
  sceneImage.src = scenePath;
  sceneImage.alt = `제${id}강 ${lecture.title} · AI 제작 교육용 장면 이미지, 실제 사업장 사진 아님`;
  $('#storySceneEyebrow').textContent = `RE:LAND · 제${id}강 / 총 ${DATA.lectures.length}강 · ${lecture.category}`;
  $('#storySceneTitle').textContent = lecture.title;
  $('#storySceneSummary').textContent = lecture.summary;
  $('#sceneImageBadge').textContent = `LESSON ${String(id).padStart(2,'0')} / STORY VISUAL`;
  $('#storySceneCaption').textContent = `제${id}강 교육을 위해 제작된 AI 이미지 · 실제 사업장 및 법률 원문 사진이 아닙니다.`;
  $('#lessonCategory').textContent = lecture.category;
  $('#lessonCount').textContent = `제${id}강 / 총 ${DATA.lectures.length}강`;
  document.title = `${lecture.title} | RE:LAND 강실장 클래스`;
  $('#heroChips').innerHTML = `<span>60강 커리큘럼</span><span>소설형 강의</span><span>실무 문서 해설</span>`;
  $('#learningIntro').textContent = lecture.scenario || lecture.summary;
  $('#briefSummary').textContent = lecture.summary;
  $('#briefDocuments').textContent = lecture.documents || '원본 자료와 작성기관을 확인하세요.';
  $('#briefPitfall').textContent = lecture.pitfall || '문서와 법령 확인 전에 결론을 내리지 마세요.';
  $('#lessonDiagram').dataset.lessonMediaId = String(id);
  $('#lessonDiagram').src = `/kang/${lecture.diagram}`;
  $('#lessonDiagram').alt = `${lecture.title}에 관한 교육용 절차 도식`;
  $('#chapterList').innerHTML = (lecture.pages || []).map((p, idx) =>
    `<article class="chapter" id="chapter-${idx+1}"><div class="chapter-index">${String(idx+1).padStart(2,'0')}</div><div><h3>${escape(p.heading)}</h3><p>${escape(p.body)}</p>${idx===2?`<div class="case-note"><strong>이 강의의 예시</strong><p>${escape(lecture.scenario)}</p><small>가상의 교육 상황이며 특정 정비사업장 또는 법적 결론이 아닙니다.</small></div>`:''}</div></article>`
  ).join('');
  $('#caseStudy').textContent = `학습용 가정: ${lecture.scenario || '공식 자료를 확보한 뒤 작성기관과 날짜별로 구분해 대조합니다.'}`;
  const docs = (lecture.documents || '공식 고시 및 관련 문서').split(/[,、，]/).map(x=>x.trim()).filter(Boolean);
  $('#docsRows').innerHTML = docs.map((d, i) => `<tr><td><strong>${escape(d)}</strong></td><td>원본 작성기관 · 발행일 확인</td><td>공식 원문 링크 및 적용 시점 대조</td><td><span class="table-index">${String(i+1).padStart(2,'0')}</span> 빈칸 점검</td></tr>`).join('');
  const makeRefs = (keys, obj) => keys.map(key => {const v=obj[key];if(!v)return '';
    try { const u=new URL(v[1]);if(u.protocol!=='https:')return '';
       return `<li><a href="${escape(u.href)}" target="_blank" rel="noopener noreferrer">${escape(v[0])} ↗</a><span>${escape(v[2])}</span></li>`; } catch{return ''} }).join('');
  $('#lawRefs').innerHTML = makeRefs(lecture.refs || [], DATA.sources.law) || '<li>관련 조문은 별도 검토 중입니다.</li>';
  $('#caseRefs').innerHTML = makeRefs(lecture.cases || [], DATA.sources.precedents) || '<li>직접 연관된 검증 완료 판례는 임의로 연결하지 않았습니다.</li>';
  $('#recapQuestions').innerHTML = [
    '이 문서의 작성기관·작성일·적용대상은 각각 무엇인가?',
    `“${lecture.title}”에서 기준시점에 따라 달라질 수 있는 항목은 무엇인가?`,
    '해당 법령·고시·조례 원문의 최신 버전을 어디에서 확인할 수 있는가?'
  ].map(x => `<li>${escape(x)}</li>`).join('');
  $('#printLesson').addEventListener('click', () => window.print());
})();
