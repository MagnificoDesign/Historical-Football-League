/* Historical Football League — offline cache.
 *
 * Registered from this directory, so its scope is this directory. That
 * matters twice over:
 *   1. A more specific scope wins, so this worker — not any origin-scope
 *      worker another project registers — serves every HFL page. Nothing
 *      else on the origin can shadow the game again.
 *   2. It never sees requests for anything outside this folder, so it
 *      cannot do to another project what was being done to this one.
 *
 * It caches the game bundle so the home-screen app opens instantly and
 * plays with no signal. It never touches IndexedDB or localStorage: saves
 * are not this worker's business and it must never eat one.
 */
var BUILD = 'v88';
var CACHE = 'hfl-' + BUILD;
var BASE = new URL('./', self.location).pathname;   // this directory

/* The versioned bundle is immutable, so it may be served from cache
   forever. index.html names the current build, so it must come from the
   network when the network is there. */
var CORE = [
  './',
  'index.html',
  'hfl-v88.html',
  'manifest.webmanifest',
  'icon-192.png',
  'icon-512.png',
  'apple-touch-icon.png'
];

function inScope(url) {
  try {
    var u = new URL(url);
    return u.origin === self.location.origin && u.pathname.indexOf(BASE) === 0;
  } catch (e) { return false; }
}
function isFont(url) {
  return /fonts\.(googleapis|gstatic)\.com/.test(url);
}

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      /* addAll is all-or-nothing; one 404 would abort the whole install and
         leave the app with no offline copy at all. Add individually. */
      return Promise.all(CORE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () { return null; });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k.indexOf('hfl-') === 0 && k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = req.url;

  /* Google Fonts: cache-first with a network fill, so the app looks right
     offline instead of falling back to a system face mid-franchise. */
  if (isFont(url)) {
    e.respondWith(
      caches.match(req).then(function (m) {
        return m || fetch(req).then(function (res) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
          return res;
        }).catch(function () { return m; });
      })
    );
    return;
  }

  if (!inScope(url)) return;               /* not ours: straight to the network */

  var u = new URL(url);
  var file = u.pathname.slice(BASE.length);
  var versioned = /^hfl-v\d+\.html$/.test(file);

  if (versioned) {
    /* immutable build: cache-first, and keep a copy the first time */
    e.respondWith(
      caches.match(req).then(function (m) {
        if (m) return m;
        return fetch(req).then(function (res) {
          if (res && res.ok) {
            var copy = res.clone();
            caches.open(CACHE).then(function (c) { c.put(req, copy); });
          }
          return res;
        });
      })
    );
    return;
  }

  /* everything else in the folder (index, manifest, icons): network-first so
     a new release is picked up, cache as the offline fallback */
  e.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (m) {
        return m || caches.match('index.html') || caches.match('./');
      });
    })
  );
});

/* The page asks for this after it has loaded a newer build. */
self.addEventListener('message', function (e) {
  if (e.data === 'hfl-skip-waiting') self.skipWaiting();
});
