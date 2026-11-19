// Minimal offline shell: network-first for pages, cache-first for built static assets.
// API calls are never cached here; evidence capture uses IndexedDB instead.
const CACHE = "veravote-shell-v1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/_next/static/")) {
    e.respondWith(caches.open(CACHE).then(async (c) => (await c.match(req)) || c.add(req).then(() => c.match(req))));
    return;
  }
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); return res; })
        .catch(() => caches.match(req).then((r) => r || caches.match("/contributor")))
    );
  }
});
