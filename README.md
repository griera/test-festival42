# 🧪 Test Festival 42 - Static Web Prototype

This repository is a **testing prototype** for a lightweight, serverless catalog and schedule service designed for **Festival 42** (Festival Gèneres Fantàstics de Barcelona).

It is built as a single-page static web app using **HTML5, Tailwind CSS v4 (compiled locally via CLI), and Vanilla JavaScript**, prioritizing performance, instant search, security (like strict Content-Security-Policy compliance) and zero maintenance overhead.

---

## 🎥 Demo & Responsive Experience

Here is a quick look at the user interface and responsive experience across different devices:

### 🖥️ Desktop

![Demo](./docs/assets/f42_demo.gif)

### 📱 Mobile

Coming soon

---

## 📂 Project Structure

```text
test-festival42/
├── index.html               # Public frontend interface (search, filters, rendering)
├── app.js                   # External frontend application logic (CSP compliant)
├── sw.js                    # Service Worker: app shell + book cover caching and update detection
├── styles.css               # Compiled, purged, and minified production Tailwind CSS
├── src/
│   └── input.css            # Tailwind CSS v4 source stylesheet (@import "tailwindcss";)
├── package.json             # Node.js project and dependencies configuration
├── package-lock.json        # Node.js locked dependency versions for exact deterministic installs
├── data.json                # Public processed dataset consumed by the web app
├── node_modules/            # Node.js local dependencies (ignored by Git)
├── data/                    # Dataset files
│   ├── catalog.csv          # Bookstore catalog (CSV dataset)
│   ├── extra_data.json      # Special activities and extra events (JSON dataset)
│   └── catalog.pdf          # PDF catalog with book covers (ignored by Git)
├── assets/                  # Public static assets
│   ├── covers/              # Extracted optimized WebP book cover images (named by EAN)
│   └── icons/               # Graphic resources and favicon
│       └── f42_32x32.png    # Festival 42 favicon
├── docs/                    # Documentation assets for the README
│   └── assets/
│       └── f42_demo.gif     # Demo video for the README
├── scripts/                 # Python development and automation tools
│   ├── generate_catalog.py  # Script for massive synthetic load testing data
│   ├── process_catalog.py   # Script to process raw catalog CSV and convert it into a JSON payload
│   ├── bump_version.py      # Script for versioning (semver for app & styles, timestamp for data; syncs index.html and sw.js)
│   └── extract_covers.py    # Script to extract book covers from distributor's PDF catalogs
├── requirements.txt         # Python package dependencies
├── .venv/                   # Python virtual environment (ignored by Git)
├── .gitignore               # Git exclusion rules
└── README.md                # Project documentation

```

---

## 🎨 Tailwind CSS Local Compilation

To maintain a strict Content-Security-Policy (CSP) without `unsafe-eval` or external script CDNs, Tailwind CSS is compiled locally using the modern **Tailwind CLI v4**.

### Setup & Compilation Steps

Ensure you have [Node.js](https://nodejs.org/) installed (recommended via [NVM](https://github.com/nvm-sh/nvm)):

1. Install project dependencies:
```bash
npm install -D tailwindcss @tailwindcss/cli

```

2. Compile the production stylesheet (`styles.css`) from your source input:
```bash
npx @tailwindcss/cli -i ./src/input.css -o ./styles.css --minify

```

3. *(Optional)* Run in watch mode during active frontend development:
```bash
npx @tailwindcss/cli -i ./src/input.css -o ./styles.css --watch

```

---

## 🐍 Python Environment & Dependencies

Python scripts that interact with PDF documents require an isolated virtual environment and package dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

---

## 🚀 How to Run Locally

Because modern browsers enforce CORS security policies on local files (`file://`), you need a lightweight local server to test it:

1. Open your terminal in the project root directory.
2. Run a local Python server:

```bash
python3 -m http.server 8000

```

3. Open your web browser and go to: `http://localhost:8000`

> 💡 The Service Worker (offline mode) only runs on HTTPS or `localhost`. While developing, enable **DevTools → Application → Service Workers → Update on reload**, so every reload uses your latest `app.js` and `sw.js` instead of the cached ones.

---

## 📋 Raw CSV Schema

The source CSV must follow the updated semicolon-delimited structure:

```text
EAN;LLIBRE;AUTORI;EDITORIAL;DISTRIBUÏDOR;TIPUS;PVP;TEMA;HORARIS

```

* **Price (`PVP`)**: Automatically defaults to `0.0` if empty or blank.
* **Quantity**: Defaults to `0` since it is absent in the raw source.
* **Schedule (`HORARIS`) / Datetime:** Automatically normalized to strict `dd/mm/yyyy` format, handling mixed format ambiguities (`dd/mm` vs `mm/dd`) using the fair date bounds (04/11/2026 - 08/11/2026). Also, automatically formatted to strict `HH:MM` by dropping trailing seconds.
* **Text Values**: Cleaned, Unicode-normalized, and stripped of trailing whitespace while preserving original raw text.

---

## 🔄 How to Update the Catalog & Test Performance

1. Place your raw semicolon-delimited CSV source file (exported from booksellers, typically in legacy `cp1252` encoding) inside your workspace.
2. **Process and convert the catalog:** Clean text, fix encoding, normalize Unicode, map headers, default missing quantities and prices to 0, verify local cover files, and generate the public `data.json` payload:

```bash
python3 scripts/process_catalog.py data/catalog_raw.csv data.json --encoding cp1252

```

*(Optional: You can pass `--replacements replacements.json` to handle specific recurring source typos, or `--no-minify` for an indented readable JSON).*

*(You can also check available options using `python3 scripts/process_catalog.py --help`)*.

*(Alternatively, to generate massive synthetic datasets for performance and scalability testing instead of real data, run:)*

```bash
python3 scripts/generate_catalog.py --books 500 --activities 50 -o data/massive_catalog.csv
python3 scripts/process_catalog.py data/massive_catalog.csv data.json

```

*(You can also check available options using `python3 scripts/generate_catalog.py --help`)*.

3. **Extract and optimize book cover images from the official PDF catalog:** Ensure your virtual environment is active, then run the extractor script to automatically crop, extract EANs, and convert covers to high-performance WebP format (PDF files are ignored by Git):

```bash
source .venv/bin/activate
python3 scripts/extract_covers.py data/catalog.pdf

```

*(You can also check available options using `python3 scripts/extract_covers.py --help`)*.

> ⚠️ Covers are cached for one year (see [Cloudflare Configuration](#️-cloudflare-configuration)) on the assumption that a cover never changes for the same EAN. If you ever regenerate existing covers (e.g. with better quality), publish them under a new URL (for example a new `assets/covers-v2/` folder), otherwise devices that already have them will keep showing the old images.

4. Compile your CSS changes if necessary (see [Tailwind CSS Local Compilation](#-tailwind-css-local-compilation)).
5. **Bump the versions** (see [Version Management Workflow](#️-version-management-workflow)): `data` if `data.json` changed, `code` if `app.js` or `styles.css` changed.
6. Commit and push `index.html`, `app.js`, `sw.js`, `styles.css`, `src/input.css`, `data.json`, and cover assets (`assets/covers/`) to deploy changes via GitHub Pages.

---

## 🏷️ Version Management Workflow

Versioned URLs (`app.js?v=…`, `styles.css?v=…`, `data.json?v=…`) let browsers and Cloudflare cache files for a year while still picking up every new release. The script `scripts/bump_version.py` keeps those versions in sync in `index.html` and in the Service Worker precache list (`sw.js`), with timezone-aware timestamps (`CET/CEST` via `Europe/Madrid`) and semantic versioning (`MAJOR.MINOR.PATCH`).

### Business Rules

1. **Data updates (`data.json`)**: a new timestamp is written to the `data.json` preload link in `index.html` (`id="dataPreload"`) and to `sw.js`. **`app.js` is not modified**: it reads the data URL and its version from that preload link, so the code version stays the same and devices only download the new data.
2. **Code updates (`app.js` / `styles.css`)**: you choose whether the change is a `patch`, `minor`, or `major` increment. Both files share the same version.
3. **Consistency check**: every run verifies that `index.html` and `sw.js` reference the same versions, and exits with code `1` if they do not or if a file or pattern is missing.

> ⚠️ Never change `app.js` or `styles.css` without bumping the code version, and never edit `?v=` values by hand: versioned files are cached for a year, so a changed file under an unchanged URL would keep being served in its old version.

### Usage Instructions

Run the script according to what you have modified (it can be launched from any directory):

* **When you update data (`data.json`):**
```bash
python3 scripts/bump_version.py data

```

* **When you make a small code/style fix (bugfix):**
```bash
python3 scripts/bump_version.py code --type patch

```

* **When you add a new feature to the code (minor update):**
```bash
python3 scripts/bump_version.py code --type minor

```

* **When you make a breaking change to the architecture/code (major update):**
```bash
python3 scripts/bump_version.py code --type major

```

* **To only verify that `index.html` and `sw.js` are aligned (changes nothing), e.g. right before deploying:**
```bash
python3 scripts/bump_version.py check

```

If both code and data changed, run `code` first and then `data`.

*(You can also check available options using `python3 scripts/bump_version.py --help`)*.

---

## ☁️ Cloudflare Configuration

The site is served by GitHub Pages behind Cloudflare (custom domain in `CNAME`). GitHub Pages does not allow custom response headers, so security headers and caching are configured in Cloudflare.

### Security Headers

**Rules → Transform Rules → Modify Response Header**, applied to all requests, with **Set static** for each header:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; media-src 'none'; frame-src 'none'; worker-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self';` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Cross-Origin-Embedder-Policy` | `require-corp` |

Notes:

* `worker-src 'self'` is required: with `'none'` the Service Worker cannot be registered and the offline mode never starts.
* `Cross-Origin-Embedder-Policy: require-corp` and the CSP both block external resources. If you ever add one (fonts, analytics, embedded videos…), allow it in the CSP **and** make sure it sends CORP or CORS headers, or it will fail to load.
* `Cross-Origin-Resource-Policy: same-origin` prevents other websites from embedding the covers and files of this site. If covers are ever moved to a subdomain or another CDN, those files need `same-site` or `cross-origin` instead.

### Caching

Goal: versioned files and covers are cached for a year, while the app shell (`index.html` and `sw.js`) is always revalidated, so open pages detect a new release within the app update check interval (`UPDATE_CHECK_INTERVAL_MS` in `app.js`, 10 minutes) after GitHub Pages publishes it.

**1. Caching → Configuration → Browser Cache TTL:** `Respect Existing Headers`

By default Cloudflare raises any browser TTL below 4 hours to 4 hours, which could keep an old `index.html` in browsers.

**2. Caching → Cache Rules**, in this order (when several rules match, the last one wins):

| # | Rule | Expression | Settings |
|---|---|---|---|
| 1 | Immutable files | `(http.request.uri.query contains "v=" and not http.request.uri.path in {"/sw.js"}) or http.request.uri.path contains "/assets/covers/"` | Eligible for cache · Edge TTL: ignore cache-control header, 1 year · Browser TTL: override origin, 1 year |
| 2 | Bypass app shell | `http.request.uri.path in {"/" "/index.html" "/sw.js"}` | Bypass cache |

Files without a rule (favicon, error pages) use the 10-minute TTL sent by GitHub Pages.

**3. Rules → Transform Rules → Modify Response Header** (Cache Rules cannot send `no-cache` or `immutable` to browsers):

| Rule | Expression | Header |
|---|---|---|
| App shell | `http.request.uri.path in {"/" "/index.html" "/sw.js"}` | `Cache-Control: no-cache, must-revalidate` |
| Immutable files | Same expression as Cache Rule 1 | `Cache-Control: public, max-age=31536000, immutable` |

**4. Purge:** run **Caching → Configuration → Purge Everything** once after changing these rules. After that, a purge after each deploy is optional: it only acts as a safety net if a file was changed without bumping its version.

### Why this works

* `sw.js` and `index.html` are never cached by Cloudflare, so a new release is visible as soon as GitHub Pages publishes it.
* `app.js?v=…`, `styles.css?v=…` and `data.json?v=…` get a new URL on every change (see [Version Management Workflow](#️-version-management-workflow)), so they can be cached for a year without serving stale content.
* Covers never change for the same EAN: new books bring new URLs and removed covers are simply no longer requested.

### Verify the headers

```bash
curl -sI https://$(cat CNAME)/sw.js | grep -iE "cache-control|cf-cache-status"
curl -sI "https://$(cat CNAME)/app.js?v=<current version>" | grep -iE "cache-control|cf-cache-status"

```

Expected:

* `sw.js` and `/`: `cache-control: no-cache, must-revalidate` and `cf-cache-status: BYPASS` or `DYNAMIC`.
* Versioned files and covers: `cache-control: public, max-age=31536000, immutable` and `cf-cache-status: HIT` from the second request on.

---

## 🛡️ Security Audit

This static prototype is audited locally using **OWASP ZAP** via Docker.

### Prerequisites

* Docker
* Local server running (`python3 -m http.server 8000`)

`--network host` with a `localhost` target lets the ZAP browser register the Service Worker (secure context), so the offline mode is also covered by the scan. `-j --client-spider` makes ZAP load the page in a headless browser and scan the requests made by `app.js`.

### Run local scan (baseline)

```bash
docker run --rm --network host -v $(pwd):/zap/wrk/:rw ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://localhost:8000 -j --client-spider -m 2 -J zap_report_local.json -r zap_report_local.html

```

### Run local scan (full)

```bash
docker run --rm --network host -v $(pwd):/zap/wrk/:rw ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py -t http://localhost:8000 -j --client-spider -m 2 -J zap_report_local_full.json -r zap_report_local_full.html

```

### Run production scan (baseline)

```bash
docker run --rm -v $(pwd):/zap/wrk/:rw ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://$(cat CNAME) -j --client-spider -m 2 -J zap_report_prod.json -r zap_report_prod.html

```

The production scan checks the real security and cache headers added by Cloudflare. If Cloudflare bot protection answers with challenges or `403` errors, temporarily add a WAF rule that skips protections for your IP during the scan.

### Run production scan (full)

> ⚠️ The full scan sends active attack payloads. Against production, the Cloudflare WAF will likely block it and may ban your IP, so prefer the local full scan and use only the baseline scan against production.

```bash
docker run --rm -v $(pwd):/zap/wrk/:rw ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py -t https://$(cat CNAME) -j --client-spider -m 2 -J zap_report_prod_full.json -r zap_report_prod_full.html

```

### 🔒 Security & CSP Compliance
To comply with a strict Content-Security-Policy (CSP) that blocks inline scripts (`unsafe-eval` / inline `<script>` tags), all application logic is completely externalized into `app.js` and loaded securely via the frontend interface. The CSP and the other security headers are set in Cloudflare (see [Security Headers](#security-headers)).

---

## 📄 License

Open-source project distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to fork or adapt for other cultural events or book fairs.
