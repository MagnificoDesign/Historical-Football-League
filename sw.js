/* HFL service worker — v191 Loop Repair.
   One served build: index.html. Old workers (hfl-sw.js and prior cache
   names) are superseded; activate deletes every foreign cache. */
const CACHE_NAME='hfl-v203-handoff-v1';
const APP_SHELL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(APP_SHELL)));
  self.skipWaiting();
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  e.respondWith(
    fetch(e.request).then(r=>{
      /* never cache an error page over a good copy */
      if(r&&r.ok){const c=r.clone();caches.open(CACHE_NAME).then(x=>x.put(e.request,c));}
      else if(r&&!r.ok){return caches.match(e.request).then(c=>c||caches.match('./index.html')).then(c=>c||r);}
      return r;
    }).catch(()=>caches.match(e.request).then(c=>c||caches.match('./index.html')))
  );
});
