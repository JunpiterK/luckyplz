/*
  Kill switch for legacy service worker.

  The previous SW was network-first for HTML/JS/CSS and cache-first for
  static assets. In practice browsers kept serving cached HTML through
  the SW even after deploys (Ctrl+Shift+R only clears HTTP cache, not
  SW cache), costing hours of "my edits aren't showing up" debugging.

  This file replaces that SW with a self-destruct routine: on activation
  every cache is deleted and the registration unregisters itself, then
  all open tabs are force-reloaded so they exit the SW's control. Fetch
  events are not intercepted at all — requests flow straight to the
  network like they would without a SW.

  Once every returning visitor has run through this once, no SW remains
  on any client and the file can be deleted. Keep it here in the
  meantime so laggards still get cleaned up on their next visit.
*/
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    } catch (err) { /* best-effort */ }
    try {
      await self.registration.unregister();
    } catch (err) { /* best-effort */ }
    try {
      const windows = await self.clients.matchAll({ type: 'window' });
      windows.forEach(w => { try { w.navigate(w.url); } catch (err) {} });
    } catch (err) { /* best-effort */ }
  })());
});

/* Intentionally no 'fetch' handler — all requests hit the network. */
