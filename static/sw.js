/* RE:LAND static-only service worker. Never cache authentication, consultations, posts or API responses. */
const CACHE='reland-shell-v1.1';
const STATIC=['/','/static/style.css','/static/app.js','/static/assets/reland-city.webp','/static/assets/icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(STATIC)).then(()=>self.skipWaiting()).catch(()=>{})));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request;
 if(req.method!=='GET'||req.url.includes('/api/')||new URL(req.url).origin!==self.location.origin)return;
 if(req.mode==='navigate'){event.respondWith(fetch(req).catch(()=>caches.match('/')));return}
 if(new URL(req.url).pathname.startsWith('/static/'))event.respondWith(caches.match(req).then(cached=>cached||fetch(req)));
});
