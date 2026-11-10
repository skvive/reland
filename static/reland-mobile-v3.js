/* Keep the mobile navigation current-page indication in sync with SPA routing. */
(()=>{
  const sync=()=>{
    const page=location.pathname.replace(/\/$/,'')||'/';
    document.querySelectorAll('.mobile-dock a').forEach(a=>{
      const active=(a.getAttribute('href').replace(/\/$/,'')||'/')===page;
      if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
    });
    const toggler=document.querySelector('.menu-button');
    if(toggler)toggler.setAttribute('aria-expanded',String(!!document.querySelector('.header.menu-open')));
  };
  document.addEventListener('click',()=>setTimeout(sync,0));
  window.addEventListener('popstate',sync);
  window.addEventListener('pageshow',sync);
  sync();
})();
