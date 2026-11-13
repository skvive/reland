'use strict';
/* RE:LAND v16: all 60 lecture images served from the same site, with fully local fallbacks.
   External image-CDN URLs were rejected after real Android screenshots showed broken images.
   Preserve every original asset; no originals are deleted or overwritten. */
(()=>{
 const prefix='/kang/assets/';
 const fmt=id=>String(id).padStart(3,'0');
 const originals=Object.freeze(Object.fromEntries(Array.from({length:60},(_,i)=>[i+1,prefix+'lessons/lesson-'+fmt(i+1)+'.webp'])));
 const illustrations=id=>prefix+'lesson-stories/story-'+fmt(id)+'.svg';
 const category=id=>prefix+'kang-clean-category-'+String(Math.ceil(id/6)).padStart(2,'0')+'-v8.webp';
 const defaultSvg=()=> 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675"><rect width="1200" height="675" fill="#e6eee9"/><path d="M0 555L260 428L460 500L700 315L950 447L1200 310V675H0Z" fill="#b5d1bd"/><path d="M105 493V290L270 197L436 290V493M520 520V210L710 112L915 210V520M965 485V315L1080 255L1170 315V485" fill="#d3e5d8" stroke="#42715d" stroke-width="18"/><path d="M90 547H1100" stroke="#245b49" stroke-width="14"/><rect x="150" y="324" width="72" height="85" rx="4" fill="#8cb69e"/><rect x="286" y="324" width="72" height="85" rx="4" fill="#8cb69e"/><rect x="615" y="254" width="82" height="98" rx="4" fill="#8cb69e"/><rect x="755" y="254" width="82" height="98" rx="4" fill="#8cb69e"/></svg>');
 const fallbackImage=defaultSvg();
 window.KANG_STORY_PHOTO_V14=originals;
 window.KANG_STORY_PHOTO_CAPTIONS_V14=Object.freeze(Object.fromEntries(Array.from({length:60},(_,i)=>[i+1,'재개발 강의 '+(i+1)+'강 교육용 에디토리얼 이미지 (실제 사업장 사진 아님)'])));
 window.KANG_MEDIA_V16=Object.freeze({get:id=>originals[id]||null,poster:id=>illustrations(id)});
 const routeId=()=>{
   const exact=location.pathname.match(/\/kang\/lectures\/lesson-(\d{3})\.html$/);
   return exact?Number(exact[1]):Number(new URLSearchParams(location.search).get('id'));
 };
 const resolvedId=img=>{
   if(!img||img.tagName!=='IMG'||img.dataset.brandHero==='1')return 0;
   let id=Number(img.dataset.lessonMediaId||img.closest('[data-lesson]')?.dataset.lesson);
   if(!Number.isInteger(id)||id<1||id>60){
     if(img.id==='storySceneImage'||img.id==='lessonDiagram'||img.closest('.rk-story'))id=routeId();
   }
   return Number.isInteger(id)&&id>=1&&id<=60?id:0;
 };
 function fallback(img){
   if(img.dataset.mediaExhausted==='1')return;
   if(img.dataset.brandHero==='1'){
     const photos=['/kang/assets/kang-class-hero-v5.webp','/kang/assets/kang-class-promo-identity-v6.webp','/kang/assets/kang-master-approved-20261111.jpg'];
     const index=photos.indexOf((img.getAttribute('src')||'').split('?')[0]);
     if(index>=photos.length-1){img.dataset.mediaExhausted='1';img.style.background='#113d32';return;}
     img.src=photos[Math.max(0,index+1)];return;
   }
   const id=resolvedId(img);
   if(!id)return;
   const choices=[originals[id],illustrations(id),category(id),fallbackImage];
   const current=img.getAttribute('src')||'';
   const index=choices.findIndex(s=>s===current||s===current.split('?')[0]);
   if(index===choices.length-1){img.dataset.mediaExhausted='1';img.style.background='#e6eee9';return;}
   const next=choices[index+1]||choices[0];
   if(!next||next===current){img.dataset.mediaExhausted='1';return;}
   img.dataset.lessonMediaId=String(id);
   img.dataset.mediaFallback=String(index+1);
   img.src=next;
 }
 document.addEventListener('error',ev=>{
   const img=ev.target;
   if(img?.tagName==='IMG')fallback(img);
 },true);
 function settle(){
   const onStandalone=location.pathname.match(/\/kang\/lectures\/lesson-(\d{3})\.html$/);
   if(onStandalone){
     const id=Number(onStandalone[1]),img=document.querySelector('.rk-story > img');
     if(img&&originals[id]){
       img.dataset.lessonMediaId=String(id);
       img.alt=window.KANG_STORY_PHOTO_CAPTIONS_V14[id];
       if(img.getAttribute('src')!==originals[id])img.src=originals[id];
     }
   }
   document.querySelectorAll('.card-visual img, #lectureImage, #storySceneImage, .rk-brand-banner img, .rk-story > img, .modal-hero, #lessonDiagram').forEach(img=>{
     const id=resolvedId(img);if(id)img.dataset.lessonMediaId=String(id);
     if(id&&img.complete&&img.naturalWidth===0)fallback(img);
   });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',settle,{once:true});
 else settle();
})();
