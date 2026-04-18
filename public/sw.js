/*
  Lucky Please Service Worker
  - HTML/JS/CSS: Network-first (always try latest, fallback to cache)
  - Images/Audio/Fonts: Cache-first (fast load, update in background)
  - Version bump CACHE_VERSION on every deploy to purge old caches
*/
const CACHE_VERSION = 20;
const CACHE_NAME = 'luckyplz-v' + CACHE_VERSION;

const PRECACHE = [
  '/',
  '/index.html',
  '/manifest.json'
];

/* Install: precache essential shell */
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(c => c.addAll(PRECACHE))
  );
  self.skipWaiting();
});

/* Activate: delete ALL old caches */
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

/* Fetch strategy based on request type */
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Skip non-GET and cross-origin
  if (e.request.method !== 'GET') return;
  if (url.origin !== location.origin) return;

  // Static assets (images, audio, fonts) → Cache-first, background update
  if (isStaticAsset(url.pathname)) {
    e.respondWith(cacheFirst(e.request));
    return;
  }

  // HTML, JS, CSS, everything else → Network-first
  e.respondWith(networkFirst(e.request));
});

function isStaticAsset(path) {
  return /\.(png|jpg|jpeg|gif|webp|svg|ico|mp3|ogg|wav|woff2?|ttf|eot)$/i.test(path);
}

/* Network-first: try network, fallback to cache */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    return cached || caches.match('/');
  }
}

/* Cache-first: use cache if available, fetch & update in background */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    // Background update (stale-while-revalidate)
    fetch(request).then(response => {
      if (response.ok) {
        caches.open(CACHE_NAME).then(c => c.put(request, response));
      }
    }).catch(() => {});
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return new Response('', { status: 404 });
  }
}
