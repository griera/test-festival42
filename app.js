'use strict';

// ==========================================
// THEME (applied first of all, so the page is painted in the chosen theme as early as possible)
// ==========================================

// Header button: automatic (follows the device) -> light -> dark. The choice is stored on this device;
// the colors of both themes live in src/theme.css.
const THEME_STORAGE_KEY = 'fair_catalog_theme';
const THEME_ORDER = ['auto', 'light', 'dark'];
const THEME_INFO = {
    auto: { icon: 'theme-auto', label: 'automàtic (segons el dispositiu)' },
    light: { icon: 'sun', label: 'clar' },
    dark: { icon: 'moon', label: 'fosc' }
};
applyTheme(getStoredTheme(), false);

function getStoredTheme() {
    try {
        const stored = localStorage.getItem(THEME_STORAGE_KEY);
        return THEME_ORDER.includes(stored) ? stored : 'auto';
    } catch (_) {
        return 'auto';
    }
}

// 'auto' removes data-theme, so src/theme.css follows the device (color-scheme: light dark)
function applyTheme(theme, store = true) {
    const root = document.documentElement;
    if (theme === 'auto') delete root.dataset.theme;
    else root.dataset.theme = theme;
    if (store) {
        try {
            if (theme === 'auto') localStorage.removeItem(THEME_STORAGE_KEY);
            else localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (_) {}
    }
    renderThemeButton(theme);
}

function cycleTheme() {
    const current = document.documentElement.dataset.theme || 'auto';
    applyTheme(THEME_ORDER[(THEME_ORDER.indexOf(current) + 1) % THEME_ORDER.length]);
}

// Icon of the current theme; the label says the current theme and the next one
function renderThemeButton(theme) {
    const button = document.querySelector('[data-action="toggle-theme"]');
    if (!button) return;
    const next = THEME_ORDER[(THEME_ORDER.indexOf(theme) + 1) % THEME_ORDER.length];
    const text = `Tema: ${THEME_INFO[theme].label}. Canvia a ${THEME_INFO[next].label}`;
    button.setAttribute('aria-label', text);
    button.title = text;
    const icon = button.querySelector('[data-role="theme-icon"]');
    if (icon) icon.className = `icon icon-${THEME_INFO[theme].icon} h-5 w-5`;
}

// ==========================================
// CONFIGURATION
// ==========================================

// Data file URL and version, taken off the data.json preload link in index.html.
// The data version is kept out of this file on purpose: app.js only changes when the code changes,
// so app.js?v=<semver> always identifies the same content and can be cached for a long time.
const DATA_URL = getDataUrl();
const TIMESTAMP_VERSION = new URL(DATA_URL, document.baseURI).searchParams.get('v') || '';

// Number of items shown per section and added by each "load more" click
const PAGE_SIZE = 30;

// Stock badge: up to this quantity a book is shown as "few units left" (amber)
const LOW_STOCK_MAX = 2;

// Delay before running a search while typing (prevents main thread blocking)
const SEARCH_DEBOUNCE_MS = 300;

// Barcode readers (USB or Bluetooth, keyboard mode) type each digit a few ms apart; people need about 100 ms per
// key even when typing fast. At least SCAN_MIN_DIGITS digits (EAN-8, UPC-A, EAN-13), each less than
// SCAN_MAX_KEY_GAP_MS after the previous one, are taken as a scan. Without a final Enter, the scan ends after
// SCAN_END_PAUSE_MS without digits.
const SCAN_MIN_DIGITS = 8;
const SCAN_MAX_KEY_GAP_MS = 50;
const SCAN_END_PAUSE_MS = 100;

// Extra wait before announcing results to screen readers, so fast typing produces one announcement, not one per pause
const RESULTS_ANNOUNCE_DELAY_MS = 500;

// Offline covers: must match COVERS_CACHE in sw.js
const COVERS_CACHE = 'fair-catalog-covers-v1';
const COVER_CHANNEL_NAME = 'fair-catalog-covers';
const COVER_REQUEST_HEADER = 'X-Fair-Cover';
const COVER_DOWNLOAD_CONCURRENCY = 6;
const COVER_TIMEOUT_MS = 20000;
const COVER_STORE_CONFIRM_MS = 5000;           // wait for the Service Worker to confirm it stored a cover
const COVER_RETRY_BASE_MS = 15000;             // backoff when the network fails but the device still reports "online"
const COVER_RETRY_MAX_MS = 5 * 60 * 1000;
const COVER_MAX_RETRY_ATTEMPTS = 8;
const COVER_DOWNLOAD_PENDING_KEY = 'fair_catalog_cover_download_pending';

// The page may stay open all day: how often to look for new data / app versions
const UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000;

// While the server is unreachable, check every minute to notice soon when the connection returns
const UNREACHABLE_CHECK_INTERVAL_MS = 60 * 1000;
// First connection/update check after page load
const FIRST_CHECK_DELAY_MS = 3000;

// After "Més tard", the new-version notice comes back after this delay
const UPDATE_REMINDER_MS = 5 * 60 * 1000;

// Captured while the script is executing (document.currentScript is null afterwards)
const APP_SCRIPT_SRC = document.currentScript ? document.currentScript.src : '';

const FILTER_BTN_BASE = 'chip';
const FILTER_BTN_IDLE = 'bg-surface text-fg-soft border-line hover:bg-raised';

// Content type configuration mapping
const eventTypesConfig = [
    { id: 'all', label: 'Tots', activeClass: 'bg-inverse text-on-inverse border-inverse-line shadow-sm' },
    { id: 'book', label: 'Llibres', icon: 'book', activeClass: 'bg-brand-600 text-on-accent border-brand-500' },
    { id: 'activity', label: 'Activitats', icon: 'microphone', activeClass: 'bg-activity-700 text-on-accent border-activity-600' }
];

// Configured event dates array for dynamic selector rendering
const eventDaysList = ['04112026', '05112026', '06112026', '07112026', '08112026'];

// Content day configuration mapping
const eventDaysConfig = [
    { id: 'all', label: 'Tots els dies', activeClass: 'bg-inverse text-on-inverse border-inverse-line shadow-sm' },
    ...eventDaysList.map((dayCode) => ({
        id: dayCode,
        label: formatDayLabel(dayCode),
        activeClass: 'bg-day-600 text-on-accent border-day-400 shadow-md'
    }))
];

// Per-section rendering settings (class names are written in full so Tailwind can detect them)
// Result grids: one column on mobile, two at 640px and wider, three at 1280px and wider (cards about 405px
// wide in the 1280px main area: the compact card of a phone, with a wider text column). PAGE_SIZE (30) and
// every "load more" fill complete rows with two or three columns.
const SECTION_META = {
    book: {
        title: 'Llibres',
        icon: 'book',
        titleClass: 'text-brand-400',
        sectionClass: '',
        listClass: 'grid gap-4 sm:grid-cols-2 xl:grid-cols-3',
        moreLabel: 'Carregar més llibres',
        moreClass: 'bg-brand-600 hover:bg-brand-500',
        // (items, previousItem) -> HTML; previousItem is the last card already shown ("load more")
        renderItems: (items) => items.map((book) => renderBookCard(book)).join('')
    },
    activity: {
        title: 'Activitats',
        icon: 'microphone',
        titleClass: 'text-activity-400',
        sectionClass: 'mt-6',
        listClass: 'grid gap-4 sm:grid-cols-2 xl:grid-cols-3',
        moreLabel: 'Carregar més activitats',
        moreClass: 'bg-activity-700 hover:bg-activity-800',
        renderItems: renderActivityItems
    }
};

// ==========================================
// GLOBAL APPLICATION STATE
// ==========================================

const state = {
    data: [],                                   // all records, each with a precomputed _search string
    hasStockData: false,                        // true when at least one book has a numeric quantity
    typeFilter: 'all',
    dayFilter: 'all',
    results: { book: [], activity: [] },        // latest filtered results, split by type
    visible: { book: PAGE_SIZE, activity: PAGE_SIZE }
};

let searchTimeout = null;
let announceTimeout = null;
// The first render (page load) is not announced: the screen reader is already reading the page
let hasRenderedResults = false;

// Offline covers: the real cache is the single source of truth for every counter shown
const coverState = {
    wanted: new Set(),          // cover URLs referenced by data.json
    cachedUrls: new Set(),      // mirror of the covers cache, kept live by Service Worker broadcasts
    addedMeanwhile: null,       // URLs announced while the cache is being re-read
    notOnServer: new Set(),     // 404/410 in the current download: retrying will not help
    waiters: new Map(),         // url -> callback waiting for the Service Worker store confirmation
    phase: 'idle',              // idle | downloading | paused-offline | paused-network | quota | done | gave-up
    renderTimer: null
};

// Manual "download all covers" run; it stays pending (also across reloads) until it completes
const coverDownload = {
    running: false,
    controller: null,
    pausedByOffline: false,
    stoppedByUser: false,
    retryTimer: null,
    retryAttempt: 0
};

// ==========================================
// INITIALIZATION
// ==========================================

async function init() {
    initFooter();
    initScrollToTop();
    bindGlobalEvents();
    initConnectionStatus();
    initStickySearch();
    initBarcodeReader();

    try {
        await loadData();
        document.getElementById('loadingIndicator').classList.add('hidden');
        document.getElementById('resultsContainer').classList.remove('hidden');

        buildFilterButtons();
        applyInitialStateFromUrl();
        executeSearch();
    } catch (error) {
        console.error('Error loading data:', error);
        // Written for the staff at the stand: what happened and what to do (technical details go to the console)
        document.getElementById('loadingIndicator').innerHTML = `
            <div class="text-center py-12 bg-surface rounded-xl border border-danger-500/40">
                <p class="text-danger-300 font-semibold">No s'ha pogut carregar el catàleg.</p>
                <p class="text-fg-muted text-sm mt-1">Comprova la connexió i torna-ho a provar.</p>
                <button type="button" data-action="reload-app" class="mt-4 px-4 py-2 rounded-lg btn-primary text-sm font-semibold transition-colors cursor-pointer disabled:opacity-70 disabled:cursor-wait focus-ring">Tornar-ho a provar</button>
            </div>
        `;
    }

    // Registered even if loading failed, so the next visit can work offline
    registerOfflineServiceWorker();
}

function initFooter() {
    const versionEl = document.getElementById('footer-version');
    if (versionEl) versionEl.textContent = getAppVersion();

    const timestampEl = document.getElementById('footer-timestamp');
    if (timestampEl) timestampEl.textContent = formatTimestamp(TIMESTAMP_VERSION);
}

// "invisible" keeps the hidden button out of the Tab order; opacity-0 alone would leave it focusable
const SCROLL_BTN_SHOWN = ['opacity-100', 'translate-y-0', 'pointer-events-auto'];
const SCROLL_BTN_HIDDEN = ['invisible', 'opacity-0', 'translate-y-4', 'pointer-events-none'];

// Scroll-to-top button: classes only change when visibility actually changes, once per frame at most
function initScrollToTop() {
    const scrollBtn = document.getElementById('scrollToTopBtn');
    if (!scrollBtn) return;

    let isShown = null;
    let ticking = false;
    const update = () => {
        ticking = false;
        const show = window.scrollY > 300;
        if (show === isShown) return;
        isShown = show;
        swapClasses(scrollBtn,
            show ? SCROLL_BTN_SHOWN : SCROLL_BTN_HIDDEN,
            show ? SCROLL_BTN_HIDDEN : SCROLL_BTN_SHOWN);
    };
    window.addEventListener('scroll', () => {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(update);
        }
    }, { passive: true });
    update();
    // Footer overlap is handled in CSS: the button lives in a sticky anchor that ends above the footer
}

function swapClasses(el, add, remove) {
    el.classList.remove(...remove);
    el.classList.add(...add);
}

// Single delegated click handler (CSP friendly, no inline handlers, safe with any author name)
function bindGlobalEvents() {
    document.addEventListener('click', (e) => {
        const target = e.target instanceof Element ? e.target : null;
        if (!target) return;

        if (target.closest('#scrollToTopBtn')) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (target.closest('[data-action="toggle-theme"]')) {
            cycleTheme();
            return;
        }

        const authorTrigger = target.closest('.author-filter-trigger');
        if (authorTrigger) {
            const authorName = authorTrigger.getAttribute('data-author');
            if (authorName) searchByAuthor(authorName);
            return;
        }

        const actionEl = target.closest('[data-action]');
        if (!actionEl) return;

        switch (actionEl.getAttribute('data-action')) {
            case 'load-more':
                loadMoreItems(actionEl.getAttribute('data-type'));
                break;
            case 'filter-type':
                setTypeFilter(actionEl.getAttribute('data-value'));
                break;
            case 'filter-day':
                setDayFilter(actionEl.getAttribute('data-value'));
                break;
            case 'prefetch-covers':
                downloadAllCovers();
                break;
            case 'stop-covers':
                stopCoverDownload();
                break;
            case 'reload-app':
                reloadApp(actionEl);
                break;
            case 'dismiss-update':
                postponeUpdateBanner();
                break;
        }
    });

    const searchInput = getSearchInput();
    if (searchInput) searchInput.addEventListener('input', handleSearch);

    // Broken covers are hidden and flagged so they can be retried when the connection returns
    document.addEventListener('error', (e) => {
        if (e.target instanceof HTMLImageElement) {
            e.target.classList.add('hidden');
            e.target.dataset.failed = '1';
        }
    }, true);

    document.addEventListener('load', (e) => {
        if (e.target instanceof HTMLImageElement) {
            e.target.classList.remove('hidden');
            delete e.target.dataset.failed;
        }
    }, true);
}

// ==========================================
// DATA
// ==========================================

async function loadData() {
    // Same URL as the preload link, so the browser reuses that download instead of starting a new one
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const json = await response.json();
    if (!Array.isArray(json)) throw new Error('data.json must contain an array');
    state.data = json.filter((item) => item && typeof item === 'object').map(prepareItem);
    state.hasStockData = state.data.some((item) => item.type === 'book' && parseStock(item.quantity) !== null);
}

const SEARCHABLE_FIELDS = ['title', 'author', 'publisher', 'distributor', 'ean', 'location', 'datetime', 'schedule'];

// Precompute one normalized string per record so each keystroke does a single includes() per item
function prepareItem(item) {
    const searchText = SEARCHABLE_FIELDS
        .map((field) => item[field])
        .filter((value) => value !== null && value !== undefined && value !== '')
        .map(normalizeText)
        .join('\u0001'); // separator that typed text never contains, so a match cannot span two fields
    return { ...item, _search: searchText, ...parseActivityDate(item) };
}

// Date of an activity ("dd/mm/yyyy HH:MM", as written by process_catalog.py):
// _when sorts activities chronologically, _day groups them under a day heading, _time is shown on the card.
// Activities without a recognizable date get null/'' and are listed last.
function parseActivityDate(item) {
    if (item.type !== 'activity') return {};
    const match = /^\s*(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?/.exec(String(item.datetime || ''));
    if (!match) return { _when: null, _day: '', _time: '' };
    const [, day, month, year, hour, minute] = match;
    const pad = (value) => String(value).padStart(2, '0');
    const dayKey = `${year}${pad(month)}${pad(day)}`;
    const time = hour !== undefined ? `${pad(hour)}:${minute}` : '';
    return { _when: Number(`${dayKey}${time ? time.replace(':', '') : '0000'}`), _day: dayKey, _time: time };
}

// Lowercase and accent-insensitive ("Barceló" matches "barcelo", "Ç" matches "c")
function normalizeText(value) {
    return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

// ==========================================
// FILTERS & SEARCH
// ==========================================

function getSearchInput() {
    return document.getElementById('searchInput');
}

// Types offered as filters: "all" plus the types the catalog really contains
function getAvailableTypes() {
    const present = new Set(state.data.map((item) => item.type));
    return eventTypesConfig.filter((typeObj) => typeObj.id === 'all' || present.has(typeObj.id));
}

function buildFilterButtons() {
    const typeContainer = document.getElementById('typeFilterContainer');
    getAvailableTypes().forEach((typeObj) => {
        typeContainer.appendChild(createFilterButton(`btn-filter-${typeObj.id}`, 'type-filter-btn', 'filter-type', typeObj));
    });

    const dayContainer = document.getElementById('dayFilterContainer');
    eventDaysConfig.forEach((dayObj) => {
        dayContainer.appendChild(createFilterButton(`btn-day-${dayObj.id}`, 'day-filter-btn', 'filter-day', dayObj));
    });
}

function createFilterButton(id, groupClass, action, config) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = id;
    btn.dataset.action = action;
    btn.dataset.value = config.id;
    btn.className = `${groupClass} ${FILTER_BTN_BASE} ${FILTER_BTN_IDLE}`;
    btn.setAttribute('aria-pressed', 'false');
    btn.innerHTML = `${config.icon ? iconHTML(config.icon, 'h-3.5 w-3.5') : ''}<span>${escapeHTML(config.label)}</span>`;
    return btn;
}

function applyInitialStateFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const initialType = urlParams.get('type');
    const initialDay = urlParams.get('day');
    const initialQuery = urlParams.get('search');

    const validTypes = getAvailableTypes().map((t) => t.id);
    setTypeFilter(validTypes.includes(initialType) ? initialType : 'all', false);

    const validDays = eventDaysConfig.map((d) => d.id);
    setDayFilter(validDays.includes(initialDay) ? initialDay : 'all', false);

    // .value is safe against XSS
    if (initialQuery) getSearchInput().value = initialQuery;
}

function highlightFilterButtons(config, idPrefix, groupClass, activeId) {
    config.forEach((obj) => {
        const btn = document.getElementById(`${idPrefix}${obj.id}`);
        if (!btn) return;
        const isActive = obj.id === activeId;
        btn.className = isActive
            ? `${groupClass} active-filter ${FILTER_BTN_BASE} ${obj.activeClass}`
            : `${groupClass} ${FILTER_BTN_BASE} ${FILTER_BTN_IDLE}`;
        btn.setAttribute('aria-pressed', String(isActive));
        // Only a specific filter (not the default 'all'): at startup the row must begin at its left edge
        if (isActive && obj.id !== 'all') revealChip(btn);
    });
}

// In the one-row filter bar of narrow screens, scroll it sideways so the active chip is fully visible
// (e.g. a link opened with ?day=08112026, whose chip would start out of view)
function revealChip(btn) {
    const row = btn.closest('[data-role="filter-row"]');
    if (!row || row.scrollWidth <= row.clientWidth) return;
    const rowBox = row.getBoundingClientRect();
    const box = btn.getBoundingClientRect();
    if (box.left < rowBox.left || box.right > rowBox.right) row.scrollLeft += box.left - rowBox.left - 16;
}

// Updates active type filter and re-runs the search filtering (by default)
function setTypeFilter(type, runSearch = true) {
    if (!eventTypesConfig.some((t) => t.id === type)) return;
    state.typeFilter = type;
    highlightFilterButtons(eventTypesConfig, 'btn-filter-', 'type-filter-btn', type);
    if (runSearch) {
        resetVisibleLimits();
        executeSearch();
    }
}

// Updates active day filter and re-runs the search filtering (by default)
function setDayFilter(dayCode, runSearch = true) {
    if (!eventDaysConfig.some((d) => d.id === dayCode)) return;
    state.dayFilter = dayCode;
    highlightFilterButtons(eventDaysConfig, 'btn-day-', 'day-filter-btn', dayCode);
    if (runSearch) {
        resetVisibleLimits();
        executeSearch();
    }
}

function resetVisibleLimits() {
    state.visible = { book: PAGE_SIZE, activity: PAGE_SIZE };
}

// Modify address bar state dynamically without page refresh
function updateUrlParams(query, type, day) {
    const url = new URL(window.location.href);
    const setOrDelete = (key, value, emptyValue) => {
        if (value && value !== emptyValue) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
    };
    setOrDelete('search', query, '');
    setOrDelete('type', type, 'all');
    setOrDelete('day', day, 'all');
    window.history.replaceState({}, '', url);
}

function matchesDay(item, targetDate) {
    return (item.datetime != null && String(item.datetime).includes(targetDate))
        || (item.schedule != null && String(item.schedule).includes(targetDate));
}

// Core search logic combining filters, text search and URL persistence
function executeSearch() {
    const rawQuery = getSearchInput().value.trim();
    const query = normalizeText(rawQuery);
    const targetDate = state.dayFilter === 'all' ? null : formatDayString(state.dayFilter);

    const book = [];
    const activity = [];
    for (const item of state.data) {
        if (state.typeFilter !== 'all' && item.type !== state.typeFilter) continue;
        if (targetDate && !matchesDay(item, targetDate)) continue;
        if (query && !item._search.includes(query)) continue;
        if (item.type === 'book') book.push(item);
        else if (item.type === 'activity') activity.push(item);
    }

    // Activities in chronological order; undated ones last, keeping their order (sort is stable)
    activity.sort((a, b) => (a._when === null) - (b._when === null) || (a._when || 0) - (b._when || 0));

    state.results = { book, activity };
    updateUrlParams(rawQuery, state.typeFilter, state.dayFilter);
    renderResults(rawQuery);

    if (hasRenderedResults) announceResults(describeResults(rawQuery));
    hasRenderedResults = true;
}

// Process text input events with timing control
function handleSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        resetVisibleLimits();
        executeSearch();
    }, SEARCH_DEBOUNCE_MS);
}

// Clicking an author name filters everything related to them immediately (no debounce needed)
function searchByAuthor(authorName) {
    clearTimeout(searchTimeout);
    getSearchInput().value = authorName;
    resetVisibleLimits();
    executeSearch();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ------------------------------------------
// Barcode readers (USB or Bluetooth, keyboard mode)
// ------------------------------------------
// A reader "types" the code and usually ends with Enter. Without help, the code was appended to the text already in
// the search box ("Minotauro9788401035777", no results), lost when the focus was elsewhere, and its Enter clicked
// the focused button. A fast burst of digits is taken as a scan (see SCAN_* in the configuration): the code replaces
// the search wherever the focus is, filters go back to "all" so the item is not hidden, and the search runs at once.
// Typing by hand is never affected: keys slower than SCAN_MAX_KEY_GAP_MS end the burst.

const scanState = { digits: '', lastKeyAt: 0, endTimer: null };

function initBarcodeReader() {
    // Capture phase: seen before the focused element handles the key (needed to stop the final Enter)
    document.addEventListener('keydown', onBarcodeKeydown, true);
}

function onBarcodeKeydown(e) {
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    const now = performance.now();
    const inBurst = now - scanState.lastKeyAt <= SCAN_MAX_KEY_GAP_MS;

    if (/^[0-9]$/.test(e.key)) {
        if (!inBurst) scanState.digits = '';     // first digit, or a slow key: a new burst starts here
        scanState.digits += e.key;
        scanState.lastKeyAt = now;
        clearTimeout(scanState.endTimer);
        scanState.endTimer = setTimeout(finishBarcodeScan, SCAN_END_PAUSE_MS);
        return;
    }
    if ((e.key === 'Enter' || e.key === 'Tab') && inBurst && scanState.digits.length >= SCAN_MIN_DIGITS) {
        e.preventDefault();                       // the reader's Enter must not click the focused button
        finishBarcodeScan();
        return;
    }
    scanState.digits = '';                        // any other key: not a scan
}

function finishBarcodeScan() {
    clearTimeout(scanState.endTimer);
    const code = scanState.digits;
    scanState.digits = '';
    if (code.length >= SCAN_MIN_DIGITS) applyScannedCode(code);
}

function applyScannedCode(code) {
    const input = getSearchInput();
    if (!input) return;
    clearTimeout(searchTimeout);                  // the digits typed into the box must not trigger their own search
    input.value = code;
    setTypeFilter('all', false);
    setDayFilter('all', false);
    resetVisibleLimits();
    executeSearch();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// RENDERING
// ==========================================

function renderResults(query) {
    const container = document.getElementById('resultsContainer');
    const html = renderSection('book') + renderSection('activity');

    if (html === '') {
        const message = query
            ? `No s'ha trobat cap resultat per "${escapeHTML(query)}".`
            : 'No hi ha resultats amb els filtres seleccionats.';
        container.innerHTML = `
            <div class="text-center py-12 card shadow-sm">
                <p class="text-fg-muted text-lg">${message}</p>
            </div>
        `;
        return;
    }
    container.innerHTML = html;
}

function renderSection(type) {
    const items = state.results[type];
    const shown = Math.min(state.visible[type], items.length);
    if (shown === 0) return '';

    const meta = SECTION_META[type];
    return `
        <section class="${meta.sectionClass}" data-section="${type}">
            <div class="flex justify-between items-center mb-3">
                <h2 class="text-xl font-bold ${meta.titleClass} flex items-center gap-2">${iconHTML(meta.icon, 'h-5 w-5')}${meta.title}</h2>
                <span class="text-xs text-fg-muted" data-role="count">${renderCountText(shown, items.length)}</span>
            </div>
            <div class="${meta.listClass}" data-role="list">${meta.renderItems(items.slice(0, shown), null)}</div>
            <div data-role="more">${renderLoadMore(type, items.length - shown)}</div>
        </section>
    `;
}

function renderCountText(shown, total) {
    return `Mostrant ${shown} de ${total}`;
}

function renderLoadMore(type, remaining) {
    if (remaining <= 0) return '';
    const meta = SECTION_META[type];
    return `
        <div class="text-center mt-6">
            <button type="button" data-action="load-more" data-type="${type}" class="${meta.moreClass} text-on-accent font-medium px-5 py-2 rounded-xl text-sm transition-colors shadow-sm cursor-pointer inline-flex flex-col items-center justify-center">
                <span>${meta.moreLabel}</span>
                <span class="text-xs opacity-90 font-normal">(${remaining} restants)</span>
            </button>
        </div>
    `;
}

// "Load more" appends only the new cards: existing cards, images and scroll position stay untouched
function loadMoreItems(type) {
    const meta = SECTION_META[type];
    const items = state.results[type];
    const section = document.querySelector(`#resultsContainer [data-section="${type}"]`);
    if (!meta || !items || !section) return;

    const start = Math.min(state.visible[type], items.length);
    const end = Math.min(start + PAGE_SIZE, items.length);
    state.visible[type] = start + PAGE_SIZE;

    const list = section.querySelector('[data-role="list"]');
    list.insertAdjacentHTML('beforeend', meta.renderItems(items.slice(start, end), items[start - 1] || null));
    section.querySelector('[data-role="count"]').textContent = renderCountText(end, items.length);
    section.querySelector('[data-role="more"]').innerHTML = renderLoadMore(type, items.length - end);

    const added = end - start;
    announceResults(type === 'book'
        ? `S'${added === 1 ? 'ha' : 'han'} carregat ${pluralize(added, 'llibre', 'llibres')} més.`
        : `S'${added === 1 ? 'ha' : 'han'} carregat ${pluralize(added, 'activitat', 'activitats')} més.`);

    // The clicked button was replaced, so focus fell back to <body> and keyboard users lost their place.
    // Move it to the first new card (or the new button); preventScroll keeps the scroll position.
    const firstNewCard = list.children[start];
    const focusTarget = (firstNewCard && firstNewCard.querySelector('button, a'))
        || section.querySelector('[data-role="more"] button');
    if (focusTarget && (document.activeElement === document.body || !document.activeElement)) {
        focusTarget.focus({ preventScroll: true });
    }
}

// ------------------------------------------
// Screen reader announcements
// ------------------------------------------

function pluralize(count, singular, plural) {
    return `${count} ${count === 1 ? singular : plural}`;
}

// "S'han trobat 12 llibres i 3 activitats." / "S'ha trobat 1 llibre."
function describeResults(query) {
    const books = state.results.book.length;
    const activities = state.results.activity.length;
    const total = books + activities;

    // Same wording as the visible empty state, so both channels say the same thing
    if (total === 0) {
        return query
            ? `No s'ha trobat cap resultat per "${query}".`
            : 'No hi ha resultats amb els filtres seleccionats.';
    }

    const parts = [];
    if (books > 0) parts.push(pluralize(books, 'llibre', 'llibres'));
    if (activities > 0) parts.push(pluralize(activities, 'activitat', 'activitats'));
    return `${total === 1 ? "S'ha trobat" : "S'han trobat"} ${parts.join(' i ')}.`;
}

function announceResults(message) {
    const region = document.getElementById('resultsAnnouncer');
    if (!region) return;
    clearTimeout(announceTimeout);
    announceTimeout = setTimeout(() => {
        // Empty it first: setting the same text twice in a row (e.g. two searches with 3 results) is not announced again
        region.textContent = '';
        setTimeout(() => { region.textContent = message; }, 50);
    }, RESULTS_ANNOUNCE_DELAY_MS);
}

// extraClass: 'inline-block py-0.5' gives stacked names a 24px touch target (WCAG 2.2, 2.5.8)
// hoverClass: hover text color and highlight background. The 2px horizontal padding keeps the highlight off the
// letters, and the equal negative margin keeps the text in its original position
function renderAuthorButton(author, hoverClass, extraClass = '') {
    return `<button type="button" class="underline cursor-pointer ${hoverClass} rounded-sm px-0.5 -mx-0.5 transition-colors text-left author-filter-trigger ${extraClass}" data-author="${escapeHTML(author)}">${safeValue(author)}</button>`;
}

// Compact card: the same information as before in less height. Publisher, distributor, category, theme and
// schedule are identified by icons and tags, with visually hidden labels for screen readers.
function renderBookCard(book) {
    return `
        <div class="card p-4 shadow-sm hover:border-brand-500 transition-colors flex gap-4">
            <!-- Cover slot: always present, so every card keeps the same layout. The book icon is visible when there is
                 no cover, while it loads, and when it cannot be loaded (the error handler hides the image). -->
            <div class="relative w-24 h-36 flex-shrink-0 rounded-lg overflow-hidden shadow bg-sunken border border-line/60">
                <div class="absolute inset-0 flex items-center justify-center text-fg-faint">${iconHTML('book', 'h-9 w-9')}</div>
                ${book.cover ? `
                    <img
                        src="${safeValue(book.cover)}"
                        alt="Coberta de ${safeValue(book.title)}"
                        class="relative w-full h-full object-cover"
                        width="96"
                        height="144"
                        loading="lazy"
                        decoding="async"
                    >
                ` : ''}
            </div>
            <div class="flex flex-col min-w-0 flex-grow">
                <h3 class="font-bold text-lg leading-snug text-fg-strong">${safeValue(book.title)}</h3>
                <p class="text-fg-soft font-medium mt-1 [&:has(.author-filter-trigger:hover)_.author-label]:text-brand-400">
                    <span class="author-label transition-colors">Autor/a:</span> ${renderBookAuthors(book.author)}
                </p>
                <div class="mt-2 flex flex-wrap items-center gap-1.5">
                    <span class="badge bg-brand-950 text-brand-300 border-brand-900">${formatPrice(book.price)}</span>
                    ${renderStockBadge(book.quantity)}
                </div>
                ${renderBookDetails(book)}
                <p class="mt-auto pt-2 text-xs text-fg-muted">EAN <span class="font-mono">${safeValue(book.ean)}</span></p>
            </div>
        </div>
    `;
}

// Publisher and distributor (icons), category and theme (tags) and signing schedule (clock), one line each
function renderBookDetails(book) {
    const lines = [];
    const trade = [renderBookDetail('building', 'Editorial', book.publisher), renderBookDetail('truck', 'Distribuïdor', book.distributor)].filter(Boolean);
    if (trade.length) lines.push(`<p>${trade.join('<span class="inline-block w-3"></span>')}</p>`);
    // Category (the kind of book) as a pill; theme (the subject, often long) as text with a tag icon
    const classification = [renderBookCategory(book.category), renderBookDetail('tag', 'Tema', book.theme)].filter(Boolean);
    if (classification.length) lines.push(`<p class="leading-6">${classification.join('<span class="inline-block w-2"></span>')}</p>`);
    if (hasText(book.schedule)) {
        lines.push(`<p>${iconHTML('clock', 'h-4 w-4 mr-1 align-[-0.2em]')}<span class="sr-only">Horaris: </span>${formatBookSchedule(book.schedule)}</p>`);
    }
    return lines.length ? `<div class="mt-2 space-y-1 text-sm text-fg-muted">${lines.join('')}</div>` : '';
}

function renderBookDetail(iconName, label, value) {
    if (!hasText(value)) return '';
    // Inline (no flex container per item): the icon is aligned with the text by vertical-align, cheaper to lay out
    return `<span title="${label}">${iconHTML(iconName, 'h-4 w-4 mr-1 align-[-0.2em]')}<span class="sr-only">${label}: </span>${safeValue(value)}</span>`;
}

function renderBookCategory(value) {
    if (!hasText(value)) return '';
    return `<span class="rounded-full bg-brand-500/15 px-2 py-0.5 text-xs font-semibold text-brand-200 ring-1 ring-inset ring-brand-400/30 [box-decoration-break:clone]" title="Categoria"><span class="sr-only">Categoria: </span>${safeValue(value)}</span>`;
}

// "dd/mm/yyyy HH:MM, ..." -> "dd/mm HH:MM · ..." (the year is the fair's own)
function formatBookSchedule(scheduleStr) {
    return String(scheduleStr).split(',').map((s) => s.trim()).filter(Boolean)
        .map((s) => escapeHTML(s.replace(/^(\d{1,2}\/\d{1,2})\/\d{4}/, '$1'))).join(' · ');
}

function hasText(value) {
    return value !== null && value !== undefined && value !== 'null' && String(value).trim() !== '';
}

// Vertical card so it fits half a row; grid items stretch to the row height and mt-auto keeps
// the location/time badge at the bottom right, aligned across cards of the same row
// Stock status of a book: the label states it in words, the color only reinforces it
const STOCK_BADGE_CLASSES = {
    out: 'bg-danger-950 text-danger-300 border-danger-800',
    low: 'bg-warning-950 text-warning-300 border-warning-800',
    ok: 'bg-success-950 text-success-300 border-success-800',
    unknown: 'bg-sunken text-fg-muted border-line'
};

// Numeric quantity of a book, or null when unknown (e.g. "No Disponible", empty, negative)
function parseStock(quantity) {
    if (typeof quantity === 'number') return Number.isInteger(quantity) && quantity >= 0 ? quantity : null;
    if (typeof quantity === 'string' && /^\s*\d+\s*$/.test(quantity)) return Number(quantity);
    return null;
}

function getStockStatus(quantity) {
    const units = parseStock(quantity);
    if (units === null) return { tone: 'unknown', label: 'Estoc desconegut' };
    if (units === 0) return { tone: 'out', label: 'Esgotat' };
    if (units <= LOW_STOCK_MAX) return { tone: 'low', label: units === 1 ? 'Queda 1' : `Queden ${units}` };
    return { tone: 'ok', label: `${units} en estoc` };
}

// An unknown stock is only shown when the catalog has real figures for some books:
// if no book has stock data, the same "unknown" badge on every card would be noise
function renderStockBadge(quantity) {
    const status = getStockStatus(quantity);
    if (status.tone === 'unknown' && !state.hasStockData) return '';
    return `<span class="badge ${STOCK_BADGE_CLASSES[status.tone]}">${escapeHTML(status.label)}</span>`;
}

// Activity cards grouped under a heading per day. previousActivity is the last card already shown, so
// "load more" does not repeat the heading of a day that continues.
function renderActivityItems(activities, previousActivity) {
    let currentDay = previousActivity ? previousActivity._day : null;
    return activities.map((activity) => {
        let heading = '';
        if (activity._day !== currentDay) {
            currentDay = activity._day;
            heading = `<h3 class="col-span-full mt-2 first:mt-0 text-sm font-semibold uppercase tracking-wide text-activity-300">${escapeHTML(formatActivityDay(activity._day))}</h3>`;
        }
        return heading + renderActivityCard(activity);
    }).join('');
}

const activityDayFormatter = new Intl.DateTimeFormat('ca-ES', { weekday: 'long', day: 'numeric', month: 'long' });

// 'YYYYMMDD' -> 'Dimecres, 4 de novembre' ('' -> 'Sense data')
function formatActivityDay(dayKey) {
    if (!dayKey) return 'Sense data';
    const date = new Date(Number(dayKey.slice(0, 4)), Number(dayKey.slice(4, 6)) - 1, Number(dayKey.slice(6, 8)));
    const label = activityDayFormatter.format(date);
    return label.charAt(0).toUpperCase() + label.slice(1);
}

// Day and time of an activity, in the "DD/MM HH:MM" format of the book schedules. Every card carries its own day:
// the day heading scrolls out of view on small screens, and search results can mix days.
// No time: "DD/MM"; not a recognizable date ("Per confirmar"): the text as it is.
function formatActivityWhen(activity) {
    if (!activity._day) return `${iconHTML('calendar', 'h-4 w-4')}${safeValue(activity.datetime)}`;
    const date = `${activity._day.slice(6, 8)}/${activity._day.slice(4, 6)}`;
    return activity._time
        ? `${iconHTML('clock', 'h-4 w-4')}${date} ${escapeHTML(activity._time)}`
        : `${iconHTML('calendar', 'h-4 w-4')}${date}`;
}

function renderActivityCard(activity) {
    const when = formatActivityWhen(activity);
    return `
        <div class="card p-4 shadow-sm hover:border-activity-500 transition-colors flex flex-col gap-3">
            <div class="min-w-0">
                <h4 class="font-bold text-fg-strong">${safeValue(activity.title)}</h4>
                <p class="text-sm text-fg-muted mt-1 [&:has(.author-filter-trigger:hover)_strong]:text-activity-400">
                    <strong class="transition-colors">Participants:</strong> ${renderActivityAuthors(activity.author)}
                </p>
            </div>
            <!-- Bottom-right badge, like the stock badge of book cards (divider line + right-aligned box) -->
            <div class="mt-auto pt-3 border-t border-line/60 flex justify-end">
                <div class="max-w-full text-right text-sm bg-activity-950 text-activity-200 border border-activity-900 px-3 py-1.5 rounded-lg">
                    <p class="flex items-center justify-end gap-1.5 break-words">${iconHTML('location', 'h-4 w-4')}${safeValue(activity.location)}</p>
                    <p class="flex items-center justify-end gap-1.5 font-semibold whitespace-nowrap">${when}</p>
                </div>
            </div>
        </div>
    `;
}

// Book authors come as "COGNOM, NOM" (the comma belongs to the name), so several authors are only split on
// unambiguous separators: ';' and ' / '. Never on ' i ', which is part of many Catalan surnames.
const BOOK_AUTHOR_SEPARATOR = /\s*;\s*|\s+\/\s+/;

// Each author of a book is its own link (search by that author), separated by '; '
function renderBookAuthors(authorStr) {
    const authors = String(authorStr || '').split(BOOK_AUTHOR_SEPARATOR).map((a) => a.trim()).filter((a) => a.length > 0);
    if (authors.length === 0) return '-';
    return authors.map((author) => renderAuthorButton(author, 'hover:text-brand-400 hover:bg-brand-highlight', 'inline-block py-0.5')).join('; ');
}

// Participants on one line separated by commas, each one a 24px-tall link (WCAG 2.2, 2.5.8)
function renderActivityAuthors(authorStr) {
    const authors = String(authorStr || '').split(',').map((a) => a.trim()).filter((a) => a.length > 0);
    if (authors.length === 0) return '-';
    return authors.map((author) => renderAuthorButton(author, 'hover:text-activity-400 hover:bg-activity-highlight', 'inline-block py-0.5')).join(', ');
}

// ==========================================
// FORMATTING UTILITIES
// ==========================================

// Decorative icon defined in src/icons.css (CSS mask painted with the text color; aria-hidden: screen readers skip it)
function iconHTML(name, classes = 'h-4 w-4') {
    return `<span class="icon icon-${name} ${classes}" aria-hidden="true"></span>`;
}

// Escape a value for HTML text or attributes (0 and false are kept, only null/undefined become '')
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/[&<>'"]/g,
        (tag) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])
    );
}

// Return '-' for null, undefined, 'null' or blank strings, but keep 0 and 0.0
function safeValue(val) {
    if (val === null || val === undefined || val === 'null') return '-';
    if (typeof val === 'string' && val.trim() === '') return '-';
    return escapeHTML(val);
}

const priceFormatter = new Intl.NumberFormat('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Missing prices show '-' instead of '0,00 €' so a missing price is never mistaken for a free book
function formatPrice(price) {
    if (price === null || price === undefined || price === '' || price === 'null') return '-';
    const num = Number(price);
    return Number.isFinite(num) ? `${priceFormatter.format(num)} €` : `${escapeHTML(price)} €`;
}

// Get date label (local date constructor, so the weekday never shifts with the time zone)
function formatDayLabel(dayCode) {
    const day = dayCode.substring(0, 2);
    const month = dayCode.substring(2, 4);
    const year = dayCode.substring(4, 8);
    const date = new Date(Number(year), Number(month) - 1, Number(day));

    const weekdays = ['Dg', 'Dl', 'Dm', 'Dc', 'Dj', 'Dv', 'Ds'];
    const months = ['Gen', 'Feb', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Des'];
    return `${weekdays[date.getDay()]} ${day} ${months[date.getMonth()]}`;
}

// Format date string DDMMYYYY -> DD/MM/YYYY
function formatDayString(dayCode) {
    if (!dayCode || dayCode === 'all') return 'all';
    return `${dayCode.substring(0, 2)}/${dayCode.substring(2, 4)}/${dayCode.substring(4)}`;
}

// Format a 14-digit timestamp into DD/MM/YYYY HH:mm:SS CET/CEST
function formatTimestamp(ts) {
    if (!ts || ts.length !== 14) return ts;

    const year = ts.slice(0, 4);
    const month = ts.slice(4, 6);
    const day = ts.slice(6, 8);
    const hour = ts.slice(8, 10);
    const minute = ts.slice(10, 12);
    const second = ts.slice(12, 14);
    const formattedDate = `${day}/${month}/${year} ${hour}:${minute}:${second}`;

    let tzName = 'CET';
    try {
        const dateObj = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
        tzName = new Intl.DateTimeFormat('en-US', {
            timeZone: 'Europe/Madrid',
            timeZoneName: 'short'
        }).formatToParts(dateObj).find((p) => p.type === 'timeZoneName')?.value || 'CET';
    } catch (_) {
        const m = parseInt(month, 10);
        tzName = (m > 3 && m < 10) ? 'CEST' : 'CET';
    }
    return `${formattedDate} ${tzName}`;
}

// The data.json preload link in index.html carries the versioned data URL (see the comment there).
// Fallback without version keeps the app working if the link is ever removed.
function getDataUrl() {
    const link = document.getElementById('dataPreload');
    return (link && link.getAttribute('href')) || 'data.json';
}

// Semantic version in the ?v= parameter of the app.js script tag
function getAppVersion() {
    const sources = APP_SCRIPT_SRC
        ? [APP_SCRIPT_SRC]
        : Array.from(document.scripts, (s) => s.src).filter((src) => src.includes('app.js'));
    for (const src of sources) {
        try {
            const v = new URL(src).searchParams.get('v');
            if (v) return v;
        } catch (_) {}
    }
    return 'n/a';
}

// ==========================================
// OFFLINE MODE
// ==========================================
// Covers are cached by the Service Worker as they are viewed. Downloading every cover is a manual
// action, meant for staff devices before the fair, on a good connection (not on the venue Wi-Fi).

function canUseServiceWorker() {
    // Browsers hide navigator.serviceWorker on plain HTTP LAN IPs
    if (!window.isSecureContext) {
        showOfflineUnavailable('Cal obrir la pàgina amb HTTPS.');
        return false;
    }
    if (!('serviceWorker' in navigator) || !('caches' in window)) {
        showOfflineUnavailable('Aquest navegador no ho permet.');
        return false;
    }
    return true;
}

function showOfflineUnavailable(detail) {
    setOfflinePanel({ tone: 'off', label: 'Mode offline no disponible', detail, progress: null, action: null });
}

async function registerOfflineServiceWorker() {
    if (!canUseServiceWorker()) return;

    // Clean up the key left by the previous prefetch implementation
    try { localStorage.removeItem('fair_catalog_last_prefetch_data_version'); } catch (_) {}

    // A new worker took control: notify only if it serves other versions than the ones this page is running
    navigator.serviceWorker.addEventListener('controllerchange', async () => {
        if (await isNewerVersionActive()) showUpdateBanner();
    });

    let registration;
    try {
        // Always the same URL: the browser detects new releases by comparing the content of sw.js, which
        // changes with every version. A versioned URL made every release install twice (once by the update
        // check with the previous URL, again by the page with the new one), downloading every file twice.
        registration = await navigator.serviceWorker.register('sw.js', { scope: './' });
    } catch (err) {
        // Happens without connection when the registered script URL differs (devices still registered by a
        // release that used versioned sw.js URLs): it cannot be downloaded yet, but the installed worker keeps
        // the offline mode working. The registration is completed on the next load with connection.
        registration = navigator.serviceWorker.controller ? await navigator.serviceWorker.getRegistration() : null;
        if (!registration) {
            console.warn('Service Worker registration failed:', err);
            showOfflineUnavailable('No s\'ha pogut activar en aquest navegador.');
            return;
        }
        console.warn('Service Worker registration postponed (offline?):', err);
    }
    schedulePeriodicUpdateChecks(registration);
    claimPageIfUncontrolled(registration);

    initCoverTracking();

    // A download started earlier (page closed, reloaded or offline at the time) continues by itself
    if (isCoverDownloadPending()) {
        setTimeout(() => downloadAllCovers({ resume: true }), 2000);
    }
}

// Look for new data/app versions periodically while the page is visible and online
// Look for new versions periodically while the page is visible. Each check also tells whether the server is
// reachable: on a Wi-Fi without internet access navigator.onLine stays true, but the check fails.
function schedulePeriodicUpdateChecks(registration) {
    let lastCheck = 0;
    const check = (force = false) => {
        if (document.visibilityState !== 'visible') return;
        if (!navigator.onLine) {
            setServerReachable(false);
            return;
        }
        // Every 10 minutes normally; every minute while unreachable, to notice soon when the connection returns
        const interval = serverReachable ? UPDATE_CHECK_INTERVAL_MS : UNREACHABLE_CHECK_INTERVAL_MS;
        if (!force && Date.now() - lastCheck < interval) return;
        lastCheck = Date.now();
        registration.update().then(() => setServerReachable(true), () => setServerReachable(false));
    };
    setInterval(check, UNREACHABLE_CHECK_INTERVAL_MS);
    document.addEventListener('visibilitychange', () => check());
    window.addEventListener('online', () => check(true));
    // First check shortly after loading, once the page and its data have had the network for themselves
    setTimeout(() => check(true), FIRST_CHECK_DELAY_MS);
}

// Shadow under the sticky search bar (narrow screens) only while it is stuck: the sentinel right above it
// has scrolled out of view
function initStickySearch() {
    const bar = document.getElementById('searchBar');
    const sentinel = document.querySelector('[data-role="search-sentinel"]');
    if (!bar || !sentinel || !('IntersectionObserver' in window)) return;
    new IntersectionObserver(([entry]) => bar.toggleAttribute('data-stuck', !entry.isIntersecting)).observe(sentinel);
}

// ------------------------------------------
// Connection notice ("Sense connexió · dades del …")
// ------------------------------------------

let serverReachable = true;

function initConnectionStatus() {
    window.addEventListener('offline', () => setServerReachable(false));
    // Without a Service Worker there are no periodic checks: trust the browser when it comes back online
    if (!('serviceWorker' in navigator)) window.addEventListener('online', () => setServerReachable(true));
    if (!navigator.onLine) setServerReachable(false);
}

function setServerReachable(reachable) {
    if (reachable === serverReachable) return;
    serverReachable = reachable;
    const status = document.getElementById('connectionStatus');
    if (!status) return;
    const chip = status.querySelector('[data-role="chip"]');
    const text = status.querySelector('[data-role="text"]');
    if (reachable) {
        chip.classList.add('hidden');
        chip.classList.remove('flex');
        text.textContent = '';
        document.documentElement.style.removeProperty('--offline-bar-h');
        return;
    }
    // The date of the data shown, so staff know how old the stock may be
    const date = formatDataDate(TIMESTAMP_VERSION);
    text.textContent = date ? `Sense connexió · dades del ${date}` : 'Sense connexió';
    chip.classList.remove('hidden');
    chip.classList.add('flex');
    // The sticky search bar goes right below the connection bar: its real height, which depends on the font size
    document.documentElement.style.setProperty('--offline-bar-h', `${chip.offsetHeight}px`);
}

// 'YYYYMMDDHHMMSS' -> 'DD/MM, HH:MM'
function formatDataDate(ts) {
    if (!ts || ts.length !== 14) return '';
    return `${ts.slice(6, 8)}/${ts.slice(4, 6)}, ${ts.slice(8, 10)}:${ts.slice(10, 12)}`;
}

// Ask the controlling worker which app/data versions it serves and compare them with this page
async function isNewerVersionActive() {
    const worker = navigator.serviceWorker.controller;
    if (!worker) return false;
    try {
        const served = await new Promise((resolve, reject) => {
            const channel = new MessageChannel();
            const timer = setTimeout(() => reject(new Error('timeout')), 3000);
            channel.port1.onmessage = (event) => {
                clearTimeout(timer);
                resolve(event.data || {});
            };
            worker.postMessage({ type: 'GET_VERSION' }, [channel.port2]);
        });
        return served.data !== TIMESTAMP_VERSION || served.app !== getAppVersion();
    } catch (_) {
        // A worker that cannot answer predates this check, so it is a different version
        return true;
    }
}

// A new Service Worker took control: new data (stock) or a new app version is ready after a reload.
// Markup and styles live in index.html; this only toggles the visibility classes.
const UPDATE_BANNER_HIDDEN = ['invisible', 'opacity-0', 'scale-95', 'pointer-events-none'];
const UPDATE_BANNER_SHOWN = ['opacity-100', 'scale-100'];
let updateReminderTimer = null;

function showUpdateBanner() {
    const banner = document.getElementById('updateBanner');
    if (!banner) return;
    clearTimeout(updateReminderTimer);
    swapClasses(banner, UPDATE_BANNER_SHOWN, UPDATE_BANNER_HIDDEN);
    // Room for the notice at the bottom: the scroll-to-top button moves up by its height plus a gap (mobile only,
    // see index.html). The notice keeps its layout while hidden, so its height is already known here
    document.documentElement.style.setProperty('--update-banner-h', `${banner.offsetHeight + 8}px`);

    // Filling the live region makes screen readers announce the notice without stealing focus. The text is read
    // off the visible notice (index.html), so it is written in one place only: "<title>. <text>"
    const announcer = banner.querySelector('[data-role="update-announcer"]');
    const message = banner.querySelector('[data-role="update-message"]');
    if (announcer && message) {
        announcer.textContent = [...message.children].map((line) => line.textContent.trim()).join('. ');
    }
}

// "Més tard" hides the notice for a while; it comes back so nobody works with stale stock all day
function postponeUpdateBanner() {
    const banner = document.getElementById('updateBanner');
    if (!banner) return;
    swapClasses(banner, UPDATE_BANNER_HIDDEN, UPDATE_BANNER_SHOWN);
    document.documentElement.style.removeProperty('--update-banner-h');
    const announcer = banner.querySelector('[data-role="update-announcer"]');
    if (announcer) announcer.textContent = '';
    clearTimeout(updateReminderTimer);
    updateReminderTimer = setTimeout(showUpdateBanner, UPDATE_REMINDER_MS);
}

function reloadApp(button) {
    button.disabled = true;
    button.textContent = 'Actualitzant…';
    window.location.reload();
}

// ------------------------------------------
// Offline panel (markup and styles in index.html; this only sets data-tone and the texts)
// ------------------------------------------

const countFormatter = new Intl.NumberFormat('ca-ES');
const percentFormatter = new Intl.NumberFormat('ca-ES', { style: 'percent', maximumFractionDigits: 0 });

// view: { tone: 'neutral' | 'progress' | 'success' | 'warning' | 'error' | 'off',
//         label, detail, progress: { cached, total } | null, action: button text | null,
//         actionName: data-action of the button (default 'prefetch-covers') }
function setOfflinePanel(view) {
    const panel = document.getElementById('offlinePanel');
    if (!panel) return;
    panel.dataset.tone = view.tone;

    // The label is a live region: only touch it when the text changes, so only state changes are announced
    const label = panel.querySelector('[data-role="label"]');
    if (label.textContent !== view.label) label.textContent = view.label;
    panel.querySelector('[data-role="detail"]').textContent = view.detail || '';

    const bar = panel.querySelector('[data-role="progress"]');
    if (view.progress && view.progress.total > 0) {
        // floor: 100 % is shown only when every cover is really stored
        const percent = Math.floor((view.progress.cached / view.progress.total) * 100);
        bar.classList.remove('invisible');
        bar.setAttribute('aria-valuenow', String(percent));
        bar.setAttribute('aria-valuetext', `${view.progress.cached} de ${view.progress.total} cobertes`);
        panel.querySelector('[data-role="progress-fill"]').style.width = `${percent}%`;
    } else {
        bar.classList.add('invisible');
    }

    const button = panel.querySelector('[data-role="action"]');
    button.classList.toggle('hidden', !view.action);
    button.classList.toggle('inline-flex', Boolean(view.action));
    if (view.action) {
        panel.querySelector('[data-role="action-label"]').textContent = view.action;
        panel.querySelector('[data-role="action-label-short"]').textContent = SHORT_ACTION_LABELS[view.action] || view.action;
        // Full text as accessible name; the short visible text is its beginning (WCAG 2.5.3, label in name)
        button.setAttribute('aria-label', view.action);
    }
    button.dataset.action = view.actionName || 'prefetch-covers';
}

// Short texts of the offline panel button for narrow screens (it shares the row with the label there)
const SHORT_ACTION_LABELS = {
    'Descarregar totes les cobertes': 'Descarregar',
    'Aturar la descàrrega': 'Aturar',
    'Reintentar ara': 'Reintentar'
};

// Unique absolute same-origin cover URLs, resolved exactly like the <img> elements resolve them
function getUniqueCoverUrls() {
    const urls = new Set();
    for (const item of state.data) {
        if (item.type !== 'book' || typeof item.cover !== 'string') continue;
        const trimmed = item.cover.trim();
        if (!trimmed) continue;
        try {
            const url = new URL(trimmed, document.baseURI);
            if (url.origin === window.location.origin) urls.add(url.href);
        } catch (_) {}
    }
    return [...urls];
}

// ------------------------------------------
// Live mirror of the covers cache
// ------------------------------------------

function initCoverTracking() {
    coverState.wanted = new Set(getUniqueCoverUrls());

    // Listen before reading the cache so nothing stored in between is missed
    if (typeof BroadcastChannel === 'function') {
        const channel = new BroadcastChannel(COVER_CHANNEL_NAME);
        channel.onmessage = (event) => {
            const msg = event.data;
            if (!msg || typeof msg.url !== 'string') return;
            if (msg.type === 'stored') {
                markCoverCached(msg.url);
                resolveCoverWaiter(msg.url, 'ok');
            } else if (msg.type === 'rejected') {
                resolveCoverWaiter(msg.url, msg.reason === 'quota' ? 'quota' : 'error');
            }
        };
    }

    // Remove covers no longer referenced by data.json (e.g. old URLs after a covers version change),
    // so devices do not keep both versions even if nobody presses "download all covers"
    pruneOrphanCovers().catch(() => {}).finally(refreshCachedCoverSet);

    // Re-read the cache when the tablet wakes up or the tab comes back (e.g. data cleared meanwhile)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') refreshCachedCoverSet();
    });
}

function markCoverCached(url) {
    coverState.cachedUrls.add(url);
    if (coverState.addedMeanwhile) coverState.addedMeanwhile.add(url);
    scheduleCoverStatusRender();
}

// Replace the mirror with the real cache contents, keeping anything announced during the read
async function refreshCachedCoverSet() {
    const addedMeanwhile = new Set();
    coverState.addedMeanwhile = addedMeanwhile;
    try {
        const cache = await caches.open(COVERS_CACHE);
        const fresh = new Set((await cache.keys()).map((request) => request.url));
        addedMeanwhile.forEach((url) => fresh.add(url));
        coverState.cachedUrls = fresh;
    } catch (_) {
        // Keep the current mirror if the cache cannot be read
    } finally {
        if (coverState.addedMeanwhile === addedMeanwhile) coverState.addedMeanwhile = null;
    }
    scheduleCoverStatusRender();
}

function countCachedCovers() {
    let cached = 0;
    for (const url of coverState.wanted) {
        if (coverState.cachedUrls.has(url)) cached++;
    }
    return cached;
}

function setCoverPhase(phase) {
    coverState.phase = phase;
    scheduleCoverStatusRender();
}

// Coalesce bursts of updates (many covers stored per second) into one DOM write
function scheduleCoverStatusRender() {
    if (coverState.renderTimer) return;
    coverState.renderTimer = setTimeout(() => {
        coverState.renderTimer = null;
        renderCoverStatus();
    }, 200);
}

function renderCoverStatus() {
    setOfflinePanel(getOfflinePanelView());
}

// Translate the cover sync state into what the panel shows
function getOfflinePanelView() {
    if (state.data.length === 0) {
        return { tone: 'neutral', label: 'Mode offline', detail: 'Les cobertes es podran desar quan es carregui el catàleg.', progress: null, action: null };
    }

    const total = coverState.wanted.size;
    if (total === 0) {
        return { tone: 'neutral', label: 'Sense cobertes', detail: 'El catàleg no inclou cobertes per desar.', progress: null, action: null };
    }

    const cached = countCachedCovers();
    const notOnServer = coverState.notOnServer.size;
    const progress = { cached, total };
    const counts = `${countFormatter.format(cached)} de ${countFormatter.format(total)} cobertes desades en aquest dispositiu`;
    const missingNote = notOnServer > 0 ? ` · ${countFormatter.format(notOnServer)} no existeixen al servidor` : '';

    switch (coverState.phase) {
        case 'downloading':
            return {
                tone: 'progress',
                label: 'Descarregant cobertes…',
                detail: `${countFormatter.format(cached)} de ${countFormatter.format(total)} · ${percentFormatter.format(cached / total)}`,
                progress,
                action: 'Aturar la descàrrega',
                actionName: 'stop-covers'
            };
        case 'stopping':
            // No button while the downloads in flight are cancelled: "download" would have no effect yet
            return { tone: 'progress', label: 'Aturant la descàrrega…', detail: `${counts}.`, progress, action: null };
        case 'paused-offline':
            return {
                tone: 'warning',
                label: 'En pausa: sense connexió',
                detail: `${counts}. Es reprendrà automàticament.`,
                progress,
                action: 'Aturar la descàrrega',
                actionName: 'stop-covers'
            };
        case 'paused-network':
            return { tone: 'warning', label: 'Problemes de xarxa', detail: `${counts}. Es tornarà a provar automàticament.`, progress, action: 'Reintentar ara' };
        case 'quota':
            return { tone: 'error', label: 'Sense espai al dispositiu', detail: `${counts}. Allibera espai i torna-ho a provar.`, progress, action: 'Tornar-ho a provar' };
        case 'gave-up':
            return { tone: 'error', label: 'Descàrrega incompleta', detail: `${counts}${missingNote}.`, progress, action: 'Tornar-ho a provar' };
        default: // idle, done
            if (cached + notOnServer >= total) {
                return {
                    tone: 'success',
                    label: 'Preparat per treballar sense connexió',
                    detail: notOnServer > 0 ? `${counts}${missingNote}.` : `Totes les cobertes desades en aquest dispositiu (${countFormatter.format(total)}).`,
                    progress,
                    action: null
                };
            }
            return { tone: 'neutral', label: 'Cobertes pendents de desar', detail: `${counts}.`, progress, action: 'Descarregar totes les cobertes' };
    }
}

// Resolves with 'ok' when the Service Worker confirms the cover is stored, 'error' or 'quota' otherwise
function waitForCoverStored(url, timeoutMs) {
    if (coverState.cachedUrls.has(url)) return Promise.resolve('ok');
    return new Promise((resolve) => {
        const timer = setTimeout(async () => {
            coverState.waiters.delete(url);
            // No broadcast (old browser, or a response served by the cache): ask the cache directly
            try {
                const cache = await caches.open(COVERS_CACHE);
                if (await cache.match(url)) {
                    markCoverCached(url);
                    resolve('ok');
                    return;
                }
            } catch (_) {}
            resolve('error');
        }, timeoutMs);

        coverState.waiters.set(url, (result) => {
            clearTimeout(timer);
            coverState.waiters.delete(url);
            resolve(result);
        });
    });
}

function resolveCoverWaiter(url, result) {
    const waiter = coverState.waiters.get(url);
    if (waiter) waiter(result);
}

// ------------------------------------------
// Manual "download all covers" (pauses offline, resumes by itself)
// ------------------------------------------

function isCoverDownloadPending() {
    try { return localStorage.getItem(COVER_DOWNLOAD_PENDING_KEY) === '1'; } catch (_) { return false; }
}

function setCoverDownloadPending(pending) {
    try {
        if (pending) localStorage.setItem(COVER_DOWNLOAD_PENDING_KEY, '1');
        else localStorage.removeItem(COVER_DOWNLOAD_PENDING_KEY);
    } catch (_) {}
}

// Ask the browser not to evict the offline covers under storage pressure (Firefox shows a prompt)
async function requestPersistentStorage() {
    try {
        if (navigator.storage && navigator.storage.persist && !(await navigator.storage.persisted())) {
            await navigator.storage.persist();
        }
    } catch (_) {}
}

// On the very first visit the page is not controlled until the new Service Worker claims it
function waitForController(timeoutMs) {
    if (navigator.serviceWorker.controller) return Promise.resolve(true);
    const controlled = new Promise((resolve) => {
        const timer = setTimeout(() => resolve(Boolean(navigator.serviceWorker.controller)), timeoutMs);
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            clearTimeout(timer);
            resolve(true);
        }, { once: true });
    });
    navigator.serviceWorker.getRegistration().then(claimPageIfUncontrolled).catch(() => {});
    return controlled;
}

// A forced reload (Ctrl+Shift+R) loads the page skipping the Service Worker, and the page would stay without one
// until the next release activates: no covers stored (the download failed with a misleading "network problems"
// message) and no offline reload. If a worker is already active, ask it to take control of this page now.
function claimPageIfUncontrolled(registration) {
    if (navigator.serviceWorker.controller || !registration || !registration.active) return;
    registration.active.postMessage({ type: 'CLAIM' });
}

// Removes stored covers that data.json no longer references: removed books, and previous versions of
// regenerated covers. A previous version is kept while the current one is not stored yet, since the
// Service Worker shows it when there is no connection (otherwise the cover would just disappear).
async function pruneOrphanCovers() {
    if (coverState.wanted.size === 0) return; // never prune against an empty list
    const cache = await caches.open(COVERS_CACHE);
    const requests = await cache.keys();
    const stored = new Set(requests.map((request) => request.url));
    const wantedByPath = new Map([...coverState.wanted].map((url) => [coverFilePath(url), url]));
    const orphans = requests.filter((request) => {
        if (coverState.wanted.has(request.url)) return false;
        const current = wantedByPath.get(coverFilePath(request.url));
        return !current || stored.has(current);
    });
    await Promise.all(orphans.map((request) => cache.delete(request)));
}

// Cover URL without its version (?v=), to match the versions of the same cover file
function coverFilePath(url) {
    const parsed = new URL(url);
    return `${parsed.origin}${parsed.pathname}`;
}

// Download only the missing covers. Downloads go through the Service Worker, which validates and stores them.
// "Aturar la descàrrega": cancels the run and forgets that it is pending, so it does not resume by itself
// on the next visit or when the connection returns (e.g. pressed by mistake on mobile data).
// Downloaded covers are kept: pressing "download all covers" again only fetches the missing ones.
function stopCoverDownload() {
    clearTimeout(coverDownload.retryTimer);
    coverDownload.retryAttempt = 0;
    setCoverDownloadPending(false);
    if (coverDownload.running && coverDownload.controller) {
        // downloadAllCovers finishes the downloads in flight and then shows the normal state
        coverDownload.stoppedByUser = true;
        coverDownload.controller.abort();
        setCoverPhase('stopping');
    } else {
        setCoverPhase('idle');
    }
    // Immediate feedback for the click (state changes are otherwise rendered in batches every 200 ms)
    renderCoverStatus();
}

async function downloadAllCovers({ resume = false } = {}) {
    if (coverDownload.running || !canUseServiceWorker()) return;
    if (coverState.wanted.size === 0) {
        renderCoverStatus();
        return;
    }

    clearTimeout(coverDownload.retryTimer);
    if (!resume) {
        coverDownload.retryAttempt = 0;
        requestPersistentStorage();
    }
    setCoverDownloadPending(true);

    if (!navigator.onLine) {
        setCoverPhase('paused-offline');
        return;
    }

    coverDownload.running = true;
    coverDownload.pausedByOffline = false;
    coverDownload.stoppedByUser = false;
    coverState.notOnServer = new Set();
    const controller = new AbortController();
    coverDownload.controller = controller;
    setCoverPhase('downloading');

    let failures = 0;
    let quotaExceeded = false;

    try {
        if (!(await waitForController(10000))) throw new Error('Service Worker not controlling the page yet');
        await pruneOrphanCovers();
        await refreshCachedCoverSet();

        const missing = [...coverState.wanted].filter((url) => !coverState.cachedUrls.has(url));
        let consecutiveErrors = 0;

        await runPool(missing, COVER_DOWNLOAD_CONCURRENCY, controller.signal, async (url) => {
            // Possibly stored meanwhile by an on-screen <img>
            if (coverState.cachedUrls.has(url)) return;

            const outcome = await downloadCover(url, controller.signal);
            if (outcome === 'aborted') return;

            if (outcome === 'missing') {
                coverState.notOnServer.add(url);
            } else if (outcome === 'quota') {
                quotaExceeded = true;
                controller.abort();
            } else if (outcome === 'error') {
                failures++;
            }

            consecutiveErrors = outcome === 'error' ? consecutiveErrors + 1 : 0;
            // The device says "online" but nothing gets through (saturated or dead Wi-Fi): pause and back off
            if (consecutiveErrors >= COVER_DOWNLOAD_CONCURRENCY * 2) controller.abort();
        });
    } catch (err) {
        console.warn('Cover download interrupted:', err);
        failures++;
    } finally {
        coverDownload.running = false;
        coverDownload.controller = null;
    }

    const stillMissing = [...coverState.wanted]
        .filter((url) => !coverState.cachedUrls.has(url) && !coverState.notOnServer.has(url)).length;

    if (coverDownload.stoppedByUser) {
        // Stopped with "Aturar": not pending any more (stopCoverDownload already cleared it)
        coverDownload.stoppedByUser = false;
        setCoverPhase('idle');
    } else if (quotaExceeded) {
        setCoverDownloadPending(false);
        setCoverPhase('quota');
    } else if (coverDownload.pausedByOffline || !navigator.onLine) {
        // The 'online' listener resumes it
        setCoverPhase('paused-offline');
    } else if (failures > 0 || stillMissing > 0) {
        scheduleCoverDownloadRetry();
    } else {
        coverDownload.retryAttempt = 0;
        setCoverDownloadPending(false);
        // Every current version is stored: remove the previous versions they replace
        await pruneOrphanCovers().catch(() => {});
        await refreshCachedCoverSet();
        setCoverPhase('done');
    }
}

// Returns 'ok', 'missing' (404/410), 'quota', 'aborted' (download paused) or 'error'
async function downloadCover(url, outerSignal) {
    const controller = new AbortController();
    const abort = () => controller.abort();
    outerSignal.addEventListener('abort', abort, { once: true });
    const timer = setTimeout(abort, COVER_TIMEOUT_MS);

    try {
        const response = await fetch(url, {
            signal: controller.signal,
            headers: { [COVER_REQUEST_HEADER]: '1' }
        });
        if (response.status === 404 || response.status === 410) return 'missing';
        if (!response.ok) return 'error';

        const type = (response.headers.get('Content-Type') || '').toLowerCase();
        // Reading the whole body lets the Service Worker receive the complete image
        const body = await response.arrayBuffer();
        if (body.byteLength === 0 || (type && !type.startsWith('image/'))) return 'error';

        // Count it only once it is really in the cache
        return await waitForCoverStored(url, COVER_STORE_CONFIRM_MS);
    } catch (_) {
        return outerSignal.aborted ? 'aborted' : 'error';
    } finally {
        clearTimeout(timer);
        outerSignal.removeEventListener('abort', abort);
    }
}

// Exponential backoff with jitter, so many devices on the same Wi-Fi do not retry in lockstep
function scheduleCoverDownloadRetry() {
    clearTimeout(coverDownload.retryTimer);
    if (coverDownload.retryAttempt >= COVER_MAX_RETRY_ATTEMPTS) {
        coverDownload.retryAttempt = 0;
        setCoverDownloadPending(false);
        setCoverPhase('gave-up');
        return;
    }
    const base = Math.min(COVER_RETRY_MAX_MS, COVER_RETRY_BASE_MS * 2 ** coverDownload.retryAttempt);
    coverDownload.retryAttempt++;
    setCoverPhase('paused-network');
    coverDownload.retryTimer = setTimeout(() => {
        // While offline, the 'online' listener takes over
        if (navigator.onLine) downloadAllCovers({ resume: true });
    }, base / 2 + Math.random() * (base / 2));
}

// Run task(item) with a fixed number of parallel workers until done or aborted
async function runPool(items, concurrency, signal, task) {
    let next = 0;
    const worker = async () => {
        while (!signal.aborted && next < items.length) {
            await task(items[next++]);
        }
    };
    await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, worker));
}

// When the connection returns, retry covers that failed to render while it was down
function repairBrokenRenderedCovers() {
    document.querySelectorAll('#resultsContainer img[data-failed]').forEach((img) => {
        const src = img.getAttribute('src');
        if (!src) return;
        delete img.dataset.failed;
        img.classList.remove('hidden');
        try {
            // _retry bypasses the in-memory image cache; the Service Worker drops it when building the cache key
            const retryUrl = new URL(src, document.baseURI);
            retryUrl.searchParams.set('_retry', Date.now().toString());
            img.src = retryUrl.href;
        } catch (_) {}
    });
}

// Pause immediately instead of letting every in-flight download time out
window.addEventListener('offline', () => {
    if (coverDownload.running && coverDownload.controller) {
        coverDownload.pausedByOffline = true;
        coverDownload.controller.abort();
    }
});

window.addEventListener('online', () => {
    repairBrokenRenderedCovers();
    if (!isCoverDownloadPending() || coverDownload.running) return;
    clearTimeout(coverDownload.retryTimer);
    coverDownload.retryAttempt = 0;
    // Random delay: every device on the venue Wi-Fi reconnects at the same moment
    coverDownload.retryTimer = setTimeout(() => downloadAllCovers({ resume: true }), 1000 + Math.random() * 3000);
});

// ==========================================
// BOOTSTRAP (last, so every const above is initialized before init() runs)
// ==========================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
