// sw.js - Service Worker: offline app shell + book covers cached as they are viewed
'use strict';

const CACHE_PREFIX = 'fair-catalog-';
const COVERS_CACHE = `${CACHE_PREFIX}covers-v1`; // also read and pruned by app.js

// Keep these ?v= versions in sync with scripts/bump_version.py and index.html
const CORE_ASSETS = [
    './',
    './index.html',
    './styles.css?v=0.9.67',
    './app.js?v=0.9.67',
    './data.json?v=20261124203019',
    './assets/icons/f42_32x32.png'
];

// Versions this worker serves, as listed in CORE_ASSETS (kept up to date by scripts/bump_version.py)
const SERVED_VERSIONS = {
    app: precachedVersion('./app.js'),
    data: precachedVersion('./data.json')
};

function precachedVersion(path) {
    const entry = CORE_ASSETS.find((asset) => asset.startsWith(`${path}?v=`));
    return entry ? new URL(entry, self.location.href).searchParams.get('v') : null;
}

// Shell cache of this release, named after the versions it serves: each release gets its own cache, and the
// previous one is deleted on activation. sw.js is always registered with the same URL (without ?v=), so the
// periodic update check and the page register the same script and each release is installed only once.
const SHELL_CACHE = `${CACHE_PREFIX}shell-${SERVED_VERSIONS.app}-${SERVED_VERSIONS.data}`;

// After this, the cached page is served and the network copy keeps updating the cache in the background
const NAVIGATION_TIMEOUT_MS = 4000;

// app.js marks its "download all covers" requests, so routing never depends on file extensions
const COVER_REQUEST_HEADER = 'X-Fair-Cover';

// Every stored or rejected cover is announced to all open tabs, so their counters mirror the real cache
const coverChannel = typeof BroadcastChannel === 'function' ? new BroadcastChannel('fair-catalog-covers') : null;

// Paths of the app page: the only navigations that may fall back to the cached app shell
const APP_PAGE_PATHS = new Set(['./', './index.html'].map((path) => new URL(path, self.location.href).pathname));

const PRECACHED_PATHS = new Set(CORE_ASSETS.map((asset) => new URL(asset, self.location.href).pathname));
const IMAGE_EXTENSIONS = /\.(avif|gif|jpe?g|png|webp)$/i;

// ==========================================
// LIFECYCLE
// ==========================================

self.addEventListener('install', (event) => {
    event.waitUntil((async () => {
        const cache = await caches.open(SHELL_CACHE);
        // 'reload' bypasses the HTTP cache so a release never precaches stale files
        await cache.addAll(CORE_ASSETS.map((asset) => new Request(asset, { cache: 'reload' })));
        await self.skipWaiting();
    })());
});

self.addEventListener('activate', (event) => {
    event.waitUntil((async () => {
        if (self.registration.navigationPreload) {
            try { await self.registration.navigationPreload.enable(); } catch (_) {}
        }
        const keys = await caches.keys();
        await Promise.all(keys
            .filter((key) => key.startsWith(CACHE_PREFIX) && key !== SHELL_CACHE && key !== COVERS_CACHE)
            .map((key) => caches.delete(key)));
        await self.clients.claim();
    })());
});

// app.js asks which versions a newly activated worker serves, to decide whether to show the update notice,
// and asks it to take control of a page loaded skipping it (see CLAIM below)
self.addEventListener('message', (event) => {
    const port = event.ports && event.ports[0];
    if (port && event.data && event.data.type === 'GET_VERSION') {
        port.postMessage(SERVED_VERSIONS);
    }
    // A forced reload (Ctrl+Shift+R) loads the page skipping this worker, and the page stays without one until the
    // next release activates: no offline reload, covers not stored. clients.claim() takes control of it now
    if (event.data && event.data.type === 'CLAIM') {
        event.waitUntil(self.clients.claim());
    }
});

// ==========================================
// ROUTING
// ==========================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    // Only same-origin requests are handled, to preserve CORS and security controls
    if (url.origin !== self.location.origin) return;

    if (request.mode === 'navigate') {
        event.respondWith(networkFirstPage(event, url));
    } else if (isCoverRequest(request, url)) {
        event.respondWith(cacheFirstCover(event, url));
    } else {
        event.respondWith(cacheFirstAsset(event));
    }
});

// <img> requests and the fetch() calls of app.js ("download all covers") both count as covers
function isCoverRequest(request, url) {
    if (request.headers.has(COVER_REQUEST_HEADER)) return true;
    if (PRECACHED_PATHS.has(url.pathname)) return false;
    return request.destination === 'image' || IMAGE_EXTENSIONS.test(url.pathname);
}

// HTML: network first with a timeout. Only the app page itself may fall back to the cached shell:
// any other path must show the real server answer, such as the custom 404 page.
async function networkFirstPage(event, url) {
    // One cache entry per page, whatever ?search=&type=&day= it was opened with
    const cacheKey = `${url.origin}${url.pathname}`;
    const isAppPage = APP_PAGE_PATHS.has(url.pathname);

    const network = (async () => {
        try {
            return (await event.preloadResponse) || (await fetch(event.request));
        } catch (_) {
            return null;
        }
    })();

    event.waitUntil(network.then((response) => (
        response && response.ok && response.type === 'basic'
            ? putInCache(SHELL_CACHE, cacheKey, response.clone())
            : null
    )));

    // A deliberate answer of the server (page, redirect, 404...) is shown as it is.
    // Redirects arrive as 'opaqueredirect' responses with status 0, so they are not treated as failures.
    const fast = await withTimeout(network, NAVIGATION_TIMEOUT_MS);
    if (fast && fast.status < 500) return fast;

    // Network down, too slow, or server error (5xx): serve the cached app if this is the app page
    if (isAppPage) {
        const cached = await caches.match(cacheKey)
            || await caches.match(new URL('./index.html', self.location.href).href)
            || await caches.match(new URL('./', self.location.href).href);
        if (cached) return cached;
    }

    // Nothing better to offer: wait for the network as long as it takes
    return (await network) || new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
}

// Covers: cache first; a network response is validated and stored after it reaches the page
async function cacheFirstCover(event, url) {
    const key = coverKey(url);
    const cache = await caches.open(COVERS_CACHE);
    const cached = await cache.match(key, { ignoreVary: true });
    if (cached) return cached;

    try {
        const response = await fetch(event.request);
        if (response.ok && response.type === 'basic') {
            event.waitUntil(storeCover(cache, key, response.clone()));
        }
        return response;
    } catch (_) {
        // Offline and this version is not stored yet (e.g. covers regenerated with a new fingerprint):
        // show the previous version of the same cover, which app.js keeps until the new one is stored.
        // Not for "download all covers" requests: they must fail, so the download retries them afterwards.
        if (!event.request.headers.has(COVER_REQUEST_HEADER)) {
            const previous = await cache.match(`${url.origin}${url.pathname}`, { ignoreSearch: true, ignoreVary: true });
            if (previous) return previous;
        }
        return new Response('', { status: 504, statusText: 'Offline' });
    }
}

// Other assets (versioned js, css, data.json, icons): cache first, network as fallback
async function cacheFirstAsset(event) {
    const { request } = event;
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok && response.type === 'basic') {
            event.waitUntil(putInCache(SHELL_CACHE, request, response.clone()));
        }
        return response;
    } catch (_) {
        // Offline and this exact version is missing: serve any previous version (e.g. an older data.json)
        const shell = await caches.open(SHELL_CACHE);
        const fallback = await shell.match(request, { ignoreSearch: true });
        return fallback || new Response('', { status: 504, statusText: 'Offline' });
    }
}

// ==========================================
// HELPERS
// ==========================================

// '_retry' is only a cache-buster used by app.js and must never create duplicate entries
function coverKey(url) {
    if (!url.searchParams.has('_retry')) return url.href;
    const clean = new URL(url.href);
    clean.searchParams.delete('_retry');
    return clean.href;
}

// Store only complete images: captive portals and saturated proxies often answer 200 with HTML
async function storeCover(cache, key, response) {
    let reason;
    try {
        const blob = await response.blob();
        reason = getCoverRejectReason(response, blob);
        if (!reason) {
            const type = (response.headers.get('Content-Type') || '').toLowerCase();
            const headers = new Headers({ 'Content-Length': String(blob.size) });
            if (type) headers.set('Content-Type', type);
            await cache.put(key, new Response(blob, { status: 200, statusText: 'OK', headers }));
            notifyCover('stored', key);
            return;
        }
    } catch (err) {
        // Cut download or storage quota: the cover will be fetched again next time
        reason = err && err.name === 'QuotaExceededError' ? 'quota' : 'network';
    }
    notifyCover('rejected', key, reason);
}

function getCoverRejectReason(response, blob) {
    if (blob.size === 0) return 'empty';
    const type = (response.headers.get('Content-Type') || '').toLowerCase();
    if (type && !type.startsWith('image/')) return 'not-image';
    // Content-Length is the compressed size when Content-Encoding is present
    const expected = Number.parseInt(response.headers.get('Content-Length') || '', 10);
    if (!response.headers.get('Content-Encoding') && expected > 0 && blob.size !== expected) return 'truncated';
    return null;
}

function notifyCover(type, url, reason) {
    try {
        if (coverChannel) coverChannel.postMessage({ type, url, reason });
    } catch (_) {}
}

async function putInCache(cacheName, key, response) {
    try {
        const cache = await caches.open(cacheName);
        await cache.put(key, response);
    } catch (_) {}
}

// Resolve to null when the promise takes longer than ms (the promise itself keeps running)
function withTimeout(promise, ms) {
    let timer;
    return Promise.race([
        promise,
        new Promise((resolve) => { timer = setTimeout(() => resolve(null), ms); })
    ]).finally(() => clearTimeout(timer));
}
