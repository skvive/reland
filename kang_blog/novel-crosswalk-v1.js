'use strict';
/* RE:LAND 강실장: 장편 경제소설 28장 ↔ 60강 학습 연계. 서사 원문 비공개 · 2026-11-15 */
(() => {
  const chapterTitles = ["두 개의 통장, 하나의 골목","가격표 뒤에 숨은 사람들","집은 왜 돈을 잡아먹기도 하는가","같은 집을 보고도 다른 그림을 그리는 이유","소문이 가장 비싼 정보일 때","발로 그린 첫 동네 지도","낡은 골목에 걸린 첫 현수막","동의서 한 장은 누구의 미래인가","추진위원회와 조합은 회사가 아니다","인가가 끝인가, 시작인가","비례율 80%가 전부가 아닌 이유","분담금 고지서가 도착한 날","남는 사람과 떠나는 사람","같은 낡음, 다른 사업","30년이 지나도 숫자는 끝나지 않는다","용적률은 마술이 아니다","공사비가 오르면 누가 부담하나","총회에서 이긴 것과 사업에서 이긴 것","법원 게시판에서 본 낮은 가격","등기부의 첫 문장을 읽는 법","세입자 한 사람이 바꾸는 계산","낙찰가보다 중요한 것은 총비용","낙찰받은 날 끝난 줄 알았다","경매물건이 정비구역에 있다면","호암산 아래, 작은 골목에서 시작된 질문","817·818·169·819, 구역을 읽는 법","인가가 난 날, 끝나지 않은 사업","돈은 골목을 먼저 지난다"];
  const chapterForLecture = [12,11,11,17,12,17,18,18,9,9,9,18,4,4,27,6,10,10,10,10,10,18,6,10,12,10,8,10,10,18,3,8,13,3,23,8,5,17,5,5,5,6,27,4,27,16,27,13,12,12,13,12,12,24,13,13,3,15,6,18];
  const categoryPrompts = {
    '분담금·감정평가':'사업비와 권리가액의 가상 숫자를 실제 사업장의 확정 금액과 구별해 읽으세요.',
    '조합 갈등·총회':'주민의 의사, 회의 기록, 적법한 의결과 행정 인가를 각각 다른 근거로 확인하세요.',
    '행정절차·정보공개':'실제 고시·공람·행정처분의 제목, 작성기관, 기준일을 분리해 확인하세요.',
    '행정심판·불복':'작품은 불복절차를 재현하지 않습니다. 학습 시 처분과 불복대상부터 따로 검토하세요.',
    '행정소송·인가취소':'작품은 소송 결과를 예측하지 않습니다. 각 사건의 처분과 제소 요건은 법률 원문이 우선입니다.',
    '민사소송·소장 읽기':'가상 인물의 계약·채무 갈등은 사실관계 정리 연습입니다. 개별 소송의 결론이 아닙니다.',
    '형사고소·사실 확인':'가상 갈등만으로 특정인의 범죄 또는 위법을 추정하지 않습니다. 사실과 평가를 분리하세요.',
    '사업단계·도면 읽기':'정비사업 조감도·구역도·인가 고시는 기능과 법적 의미가 서로 다를 수 있습니다.',
    '분양·관리처분':'작품의 가상 분양·분담금 숫자는 실제 조합원 자격이나 부담액을 정하지 않습니다.',
    '보상·이주·갈등관리':'집을 가진 사람과 사는 사람의 시간표를 분리하고, 권리와 주거의 문제를 함께 살펴보세요.'
  };
  const render = () => {
    const lessonId = Number(new URLSearchParams(window.location.search).get('id'));
    const lesson = window.KANG_DATA?.lectures?.find(x => x.id === lessonId);
    const scene = document.getElementById('episodeScene');
    if (!lesson || !scene || !Number.isInteger(lessonId) || lessonId < 1 || lessonId > 60 || document.getElementById('novelBridge')) return;
    const chapterNo = chapterForLecture[lessonId - 1];
    const title = chapterTitles[chapterNo - 1];
    const section = document.createElement('section');
    section.id = 'novelBridge';
    section.className = 'content-panel reland-novel-bridge';
    section.setAttribute('aria-labelledby', 'novelBridgeTitle');
    section.innerHTML = '<span class="novel-bridge-kicker">RE:LAND · 부자동네 가난한 동네 · 이야기와 강의</span>' +
      '<h2 id="novelBridgeTitle"></h2>' +
      '<p class="novel-bridge-intro"></p>' +
      '<div class="novel-bridge-grid"><div><strong>이 강의에서 확인할 점</strong><p class="novel-bridge-topic"></p></div>' +
      '<div><strong>소설을 읽을 때의 관점</strong><p class="novel-bridge-guide"></p></div></div>' +
      '<p class="novel-bridge-note">※ 편집 중인 28장 장편 경제소설과의 주제 연계 안내입니다. 소설 원문을 게시하거나 특정 사업·인물의 법률적 사실을 확정하는 설명이 아닙니다. 실제 고시·법령은 공식 자료를 확인하세요.</p>';
    section.querySelector('h2').textContent = '소설로 이어 읽기 · 제' + chapterNo + '장 「' + title + '」';
    section.querySelector('.novel-bridge-intro').textContent = '제' + lessonId + '강 「' + lesson.title + '」를 읽은 다음, 같은 경제적 문제를 사람의 선택과 생활 속 갈등으로 생각해 보는 연계 장입니다.';
    section.querySelector('.novel-bridge-topic').textContent = lesson.summary || lesson.title;
    section.querySelector('.novel-bridge-guide').textContent = categoryPrompts[lesson.category] || '가상 서사와 실제 공공기록의 차이를 구분해 읽으세요.';
    scene.insertAdjacentElement('afterend', section);
    const nav = document.querySelector('.course-side .side-block');
    if(nav && !nav.querySelector('a[href="#novelBridge"]')){
      const link = document.createElement('a');link.href = '#novelBridge';link.textContent = '소설 연계 읽기';
      nav.appendChild(link);
    }
  };
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded',render,{once:true});
  else render();
  window.KANG_NOVEL_BRIDGE = Object.freeze({edition:'v4.8',chapterTitles,chapterForLecture});
})();
