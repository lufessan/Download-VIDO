const CACHE_NAME = 'arkan-ai-v1';
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/favicon.ico',
  '/static/favicon-32.png',
  '/static/favicon-16.png',
  '/static/favicon-small.png',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/background-optimized.jpg',
  '/static/arkan-logo-optimized.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Don't cache POST requests or API calls
  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/download') || 
      url.pathname.startsWith('/estimate') ||
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/admin')) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);

      // Return cached first, fetch in background (stale-while-revalidate)
      return cached || fetchPromise;
    })
  );
});
