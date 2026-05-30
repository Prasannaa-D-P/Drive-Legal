// DriveLegal PWA Service Worker
// Implements Cache-First caching strategy to enable 100% offline functionality.

const CACHE_NAME = 'drivelegal-cache-v1';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'index.css',
  'app.js',
  'chatbot.js',
  'calculator.js',
  'radar.js',
  'data/laws_india.js',
  'manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install Event - Pre-cache all essential shell assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Pre-caching static app shell assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate Event - Clean up stale cache assets from previous builds
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache: ', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - Intercept resource fetches to serve from cache or network dynamically
self.addEventListener('fetch', event => {
  // Only handle GET requests (browsers can throw errors on POST caching)
  if (event.request.method !== 'GET') return;

  // Skip caching for backend API requests
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached file if found
        if (cachedResponse) {
          return cachedResponse;
        }

        // Otherwise fetch from web and dynamically cache the new resource
        return fetch(event.request)
          .then(networkResponse => {
            // Check if response is valid (don't cache error states or third-party opaque assets)
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }

            // Clone response to put one copy in cache and return the other
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          })
          .catch(() => {
            // If fetch fails and resource is an HTML document, we can return index.html as a fallback
            if (event.request.headers.get('accept').includes('text/html')) {
              return caches.match('index.html');
            }
          });
      })
  );
});
