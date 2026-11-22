/* RE:LAND educational material copyright notices and modest user-interface deterrence.
   These controls do not provide DRM or prevent screen capture. */
(()=>{'use strict';
 const protectedPage=/^\/rights-analysis\/(?:lesson-\d{1,2}|workbook|instructor|slides)\/?$/.test(location.pathname);
 document.addEventListener('contextmenu',e=>{if(!protectedPage && e.target.closest('img')){e.preventDefault()}});
 document.addEventListener('dragstart',e=>{if(e.target.closest('img'))e.preventDefault()});
 if(!protectedPage)return;
 document.documentElement.classList.add('reland-protected-reading');
 const style=document.createElement('style');style.textContent=`
 .reland-protected-reading .hero-art img,.reland-protected-reading .article img,.reland-protected-reading .aux-card img{-webkit-user-drag:none;user-select:none}
 .reland-copyright-watermark{position:fixed;right:12px;bottom:10px;padding:6px 10px;border:1px solid #d7dfdca0;border-radius:8px;background:#fffffff0;color:#73837b;font:600 10px/1.4 system-ui,sans-serif;pointer-events:none;z-index:40}
 @media print{body>*{display:none!important}body::before{content:'© RE:LAND · LEXID — 온라인 열람 전용 교재. 인쇄 및 재배포는 허가가 필요합니다.';display:block!important;color:#223b39;font:18px/1.8 sans-serif;padding:40px}}
 `;document.head.appendChild(style);
 document.addEventListener('contextmenu',e=>{if(e.target.closest('.lesson-block,.article,.aux-card,.hero-art')){e.preventDefault();notify('교재는 온라인 열람 전용입니다.')}});
 document.addEventListener('dragstart',e=>{if(e.target.closest('img'))e.preventDefault()});
 document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&['s','p'].includes(e.key.toLowerCase()) && !/INPUT|TEXTAREA/.test(e.target.tagName)){e.preventDefault();notify('온라인 열람 전용 교재입니다.')}});
 function notify(message){let t=document.getElementById('reland-copyright-toast');if(!t){t=document.createElement('div');t.id='reland-copyright-toast';t.style.cssText='position:fixed;bottom:52px;right:12px;max-width:300px;border-radius:8px;padding:10px 14px;background:#183b37;color:white;font-size:12px;z-index:50;box-shadow:0 8px 24px #0002';t.setAttribute('role','status');document.body.appendChild(t)}t.textContent=message;clearTimeout(t._timer);t._timer=setTimeout(()=>t.remove(),2400)}
 const mark=document.createElement('div');mark.className='reland-copyright-watermark';mark.textContent='© RE:LAND · LEXID | 개인 학습용';document.body.appendChild(mark);
})();
