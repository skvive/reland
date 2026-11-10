/* RE:LAND v4: never cache auth, user data, Blogger API or private feeds. */
const CACHE='reland-shell-v4-20261110';
const STATIC=['/static/style.css','/static/reland-v2.css','/static/app.js','/static/reland-v2.js','/static/assets/logo-reland.svg','/static/assets/reland-home-city-v2.webp','/static/assets/icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(STATIC).catch(()=>{})).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('reland-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request,url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 if(req.mode==='navigate'){event.respondWith(fetch(req).catch(()=>caches.match('/')));return}
 if(!url.pathname.startsWith('/static/'))return;
 event.respondWith(fetch(req).then(resp=>{if(resp.ok){const clone=resp.clone();caches.open(CACHE).then(c=>c.put(req,clone)).catch(()=>{})}return resp}).catch(()=>caches.match(req)));
});