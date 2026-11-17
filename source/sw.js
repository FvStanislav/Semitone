const CACHE='semitone-v04-mobile-1';
const ROOT=new URL('./',self.location.href).href;
const SHELL=['./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png','./icons/apple-touch-icon.png'].map(x=>new URL(x,ROOT).href);
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await c.addAll(SHELL);await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('semitone-')&&k!==CACHE)await caches.delete(k);await self.clients.claim()})()));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
if(e.request.mode==='navigate'){e.respondWith((async()=>{try{const r=await fetch(e.request);if(r.ok){const c=await caches.open(CACHE);await c.put(SHELL[0],r.clone())}return r}catch{const c=await caches.open(CACHE);return await c.match(SHELL[0])||Response.error()}})());return}
if(SHELL.includes(e.request.url))e.respondWith((async()=>{const c=await caches.open(CACHE);return await c.match(e.request)||fetch(e.request)})());});