'use strict';
/** The 24 titles/order/page starts are verified against LEXID v1.4 556-page source PDF. */
const COURSE_PDF = 'https://drive.google.com/file/d/10z_Hub42N03pO_oVRweJF-NGOK6-moF-/view';
const LESSONS = [
 [1,'권리분석의 역할과 판단 순서','소유·점유·채권·공법 제한을 구분해 분석 순서를 익힙니다.','물건 표시·등기사항증명서·건축물대장','권리·서류 확인표'],
 [2,'물권과 채권의 기초','물권과 채권의 차이, 권리의 상대방과 공시 방법을 학습합니다.','등기기록·계약서·권리자 정보','권리 유형 구분표'],
 [3,'등기사항증명서 읽는 순서','표제부·갑구·을구의 구조와 확인 순서를 실습합니다.','토지·건물 등기사항증명서','등기 기록 분석표'],
 [4,'권리순위와 기준권리','권리 설정일과 우선순위, 경매시 기준이 되는 권리를 대조합니다.','등기사항증명서·임대차 확인 자료','권리순위 타임라인'],
 [5,'소유권·공유지분·상속','단독·공유·상속의 거래 권한과 확인 서류를 구분합니다.','등기기록·상속관계 자료·위임장','소유 및 처분 권한표'],
 [6,'저당권과 근저당권','채권최고액과 실제 피담보채무를 구별하고 담보 위험을 분석합니다.','을구 등기·채권채무 증빙','담보권 검토표'],
 [7,'가압류·압류·가처분','보전·집행 절차에 따른 차이와 거래상 확인 사항을 살핍니다.','관련 결정문·사건번호·등기','처분 제한 위험표'],
 [8,'주택임대차 대항력','주택의 인도·전입과 확정일자 등 보호 요건을 비교합니다.','임대차계약서·전입 및 점유 자료','대항력 요건 체크'],
 [9,'소액임차인 최우선변제','기준 시점과 지역별 요건·보증금 범위를 확인하는 법을 익힙니다.','임대차내역·담보설정일·적용 기준','최우선변제 검토표'],
 [10,'상가건물 임대차 분석','상가임차인의 계약·점유·사업자등록 관련 권리를 점검합니다.','상가 임대차계약·사업자등록 관련 자료','상가 임차권 분석표'],
 [11,'법원경매 핵심 서류 3종','매각물건명세서·현황조사서·감정평가서의 역할을 구별합니다.','법원경매 공개서류 3종','서류 교차검증 시트'],
 [12,'경매 절차와 입찰 준비','매각기일·보증금·입찰표·잔금 일정을 단계별로 확인합니다.','매각 공고·입찰 안내·가상 입찰표','모의 입찰 준비표'],
 [13,'경매의 인수·소멸 위험','선순위와 비등기 권리의 인수 가능성을 조심스럽게 검토합니다.','등기기록·법원 경매서류·점유 조사','인수 위험 목록'],
 [14,'배당요구와 배당 계산 기초','배당요구 종기와 순위·배당표를 가상 금액으로 연습합니다.','배당요구 안내·가상 채권 명세','배당 계산표'],
 [15,'점유·명도·인도 위험','점유자의 법적 지위와 적법한 인도 절차를 구별합니다.','점유관계 자료·매각 조건','점유 위험 검토표'],
 [16,'유치권과 법정지상권','신고나 표지만으로 권리 성립을 단정하지 않는 판단법을 익힙니다.','공사대금 자료·건물/토지 등기','비등기 권리 검토표'],
 [17,'건축물·토지 공적장부 대조','건축물대장·토지대장·지적도와 등기 표시의 차이를 확인합니다.','건축물대장·토지대장·지적도','공적장부 대조표'],
 [18,'토지이용계획과 공법상 제한','용도지역·규제·허가 여부를 원문 기준으로 조사합니다.','토지이용계획확인서·관련 고시','공법상 제한 목록'],
 [19,'재개발·재건축 권리 분석','정비사업 단계와 권리변동, 조합원·임차인 지위를 구분합니다.','정비구역 고시·계획·조합 관련 문서','정비사업 권리 체크'],
 [20,'공매·체납처분의 구조','법원경매와 공매·체납처분의 절차·권리 검토 차이를 비교합니다.','공매공고·체납처분 서류','경매·공매 비교표'],
 [21,'조세·법정기일과 우선순위','조세채권과 선후 순위를 적용 시점에 맞춰 조사합니다.','세금 관련 증빙·법정기일 확인 자료','조세채권 확인표'],
 [22,'투자수익·입찰상한 계산','취득·보유·매각비용을 구분해 입찰상한을 계산합니다.','가상 낙찰가·비용·예상수익 자료','ROI·입찰상한 계산표'],
 [23,'통합 권리분석 보고서 작성','객관적 사실과 가정·미확인 사항을 나눠 최종 보고서를 작성합니다.','등기·계약·공법 자료 종합','근거 기반 권리분석 보고서'],
 [24,'종합 사례연습과 모의평가','가상 부동산의 권리·배당·투자 위험을 종합 검토합니다.','모의사례 및 앞선 실습 자료','최종 모의평가 결과표']
];
const names={1:'PART 01 · 권리의 기초',2:'PART 02 · 임대차와 경매 기초',3:'PART 03 · 경매·공법',4:'PART 04 · 투자·보고서 실전'};
const pageOf=(n)=>5+(n-1)*23;
const esc=(str)=>String(str).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const stage=(n)=>Math.ceil(n/6);
const list=document.getElementById('courseList');
const empty=document.getElementById('courseEmpty');
const search=document.getElementById('courseSearch');
const buttons=[...document.querySelectorAll('.filter')];
let selected='all';
function render(){
  const q=(search.value||'').normalize('NFKC').trim().toLocaleLowerCase('ko');
  const matches=LESSONS.filter(x=>(selected==='all'||stage(x[0])===Number(selected))&&(!q||[x[1],x[2],x[3],x[4],String(x[0])].join(' ').normalize('NFKC').toLocaleLowerCase('ko').includes(q)));
  list.innerHTML=matches.map(([num,title,desc,docs,result])=>{
    const page=pageOf(num), tag=names[stage(num)];
    return `<details class="course-card" id="lesson-${String(num).padStart(2,'0')}"><summary aria-label="${esc(num+'강 '+title+' 상세 학습 내용')}"><span class="course-no">${String(num).padStart(2,'0')}</span><span class="course-main"><small>${esc(tag)}</small><strong>${esc(title)}</strong></span><span class="course-chevron" aria-hidden="true">+</span></summary><div class="course-body"><p>${esc(desc)}</p><dl><dt>확인 자료</dt><dd>${esc(docs)}</dd><dt>학습 결과</dt><dd>${esc(result)}</dd><dt>원본 교재</dt><dd>v1.4 PDF ${page}쪽부터 (약 23쪽)</dd></dl><a class="lesson-link" target="_blank" rel="noopener noreferrer" href="${COURSE_PDF}#page=${page}">이 강의의 교재 페이지 열기 ↗</a></div></details>`;
  }).join('');
  empty.hidden=matches.length!==0;
}
function selectFilter(next){selected=next;buttons.forEach(btn=>{let active=btn.dataset.filter===next;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active))});render()}
buttons.forEach(btn=>btn.addEventListener('click',()=>selectFilter(btn.dataset.filter)));
search.addEventListener('input',render);
render();
const query=new URLSearchParams(window.location.search);const lesson=Number(query.get('lesson'));
if(Number.isInteger(lesson)&&lesson>=1&&lesson<=24){const s=stage(lesson); if(!document.getElementById(`lesson-${String(lesson).padStart(2,'0')}`))selectFilter(String(s));const el=document.getElementById(`lesson-${String(lesson).padStart(2,'0')}`);if(el){el.open=true;requestAnimationFrame(()=>el.scrollIntoView({block:'center'}))}}
