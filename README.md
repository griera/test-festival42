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
├── 404.html                 # Custom "not found" page served by GitHub Pages (no scripts, CSP compliant)
├── app.js                   # External frontend application logic (CSP compliant)
├── sw.js                    # Service Worker: app shell + book cover caching and update detection
├── styles.css               # Compiled, purged, and minified production Tailwind CSS
├── src/
│   └── input.css            # Tailwind CSS v4 source stylesheet (@import "tailwindcss";)
├── package.json             # Node.js project and dev dependencies (Tailwind CLI, esbuild, html-minifier-terser)
├── package-lock.json        # Node.js locked dependency versions for exact deterministic installs
├── data.json                # Public processed dataset consumed by the web app
├── node_modules/            # Node.js local dependencies (ignored by Git)
├── data/                    # Dataset files
│   ├── catalog.csv          # Bookstore catalog (CSV dataset)
│   ├── replacements.json    # Recurring text fixes applied to the raw CSV (process_catalog.py --replacements)
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
│   ├── cover_version.py     # Content fingerprint of a cover, used in its URL (?v=); shared by process_catalog and bump_version
│   ├── bump_version.py      # Script for versioning (semver for app & styles, timestamp for data; syncs index.html and sw.js; checks cover versions)
│   └── extract_covers.py    # Script to extract book covers from distributor's PDF catalogs
├── requirements.txt         # Python package dependencies
├── .venv/                   # Python virtual environment (ignored by Git)
├── .github/
│   └── workflows/
│       └── deploy-pages.yml # GitHub Actions workflow: publishes only the static site files to GitHub Pages
├── .gitignore               # Git exclusion rules (including the temporary _site/ folder of the deploy workflow)
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
* **Quantity**: Set to `No Disponible` since it is absent in the raw source.
* **Schedule (`HORARIS`) / Datetime:** Automatically normalized to strict `dd/mm/yyyy` format, handling mixed format ambiguities (`dd/mm` vs `mm/dd`) using the fair date bounds (04/11/2026 - 08/11/2026). Also, automatically formatted to strict `HH:MM` by dropping trailing seconds.
* **Text Values**: Cleaned, Unicode-normalized, and stripped of trailing whitespace while preserving original raw text.

---

## 🔄 How to Update the Catalog & Test Performance

1. Place your raw semicolon-delimited CSV source file (exported from booksellers, typically in legacy `cp1252` encoding) inside your workspace.
2. **Extract and optimize book cover images from the official PDF catalog:** Ensure your virtual environment is active, then run the extractor script to automatically crop, extract EANs, and convert covers to high-performance WebP format (PDF files are ignored by Git):

```bash
source .venv/bin/activate
python3 scripts/extract_covers.py data/catalog.pdf

```

Covers are saved as WebP at **quality 75** with the most efficient encoder effort (**method 6**): about half the size of quality 85, with no visible difference at the 96×144 px size they are shown at. Images taller than 432 px (3× that height, enough for the densest phone screens) are downscaled, never upscaled. At the end, the script prints the total and average size, which helps compare settings:

```bash
python3 scripts/extract_covers.py data/catalog.pdf --quality 65 --output /tmp/covers_q65/

```

*(You can also check available options using `python3 scripts/extract_covers.py --help`)*.

> ℹ️ **Cover URLs and caching.** Covers are cached for one week by Cloudflare and browsers, and kept by the Service Worker for offline use (see [Cloudflare Configuration](#️-cloudflare-configuration)), so a changed image under the same URL would not reach devices that already have it. That is why each cover URL carries a **fingerprint of its content**, `assets/covers/<EAN>.webp?v=<fingerprint>` (first 8 characters of its SHA-256, computed by `scripts/cover_version.py`). `process_catalog.py` writes it, so there is nothing to remember: an unchanged cover keeps its URL and is never downloaded again, while a regenerated cover with a different content (another quality, a new catalog edition…) gets a new URL that every device downloads, and devices delete the old one on their next visit. The only rule is the order: **extract the covers first, then run `process_catalog.py`**. If you forget, `bump_version.py check` reports the outdated covers and the deployment workflow stops before publishing.

3. **Process and convert the catalog** (always after extracting the covers, so `data.json` points to the current cover files)**:** Clean text, fix encoding, normalize Unicode, map headers, set missing quantities to `No Disponible` and missing prices to 0, link each book to its local cover file through a fingerprinted URL (see the covers note above), and generate the public `data.json` payload:

```bash
python3 scripts/process_catalog.py data/catalog_raw.csv data.json --encoding cp1252

```

*(Optional: `--no-minify` writes an indented, readable JSON).*

**Recurring source typos** are fixed with `--replacements data/replacements.json`, a JSON object that maps each wrong text to its correction:

```json
{
  "Ciencia-ficcio": "Ciència-ficció",
  "Editorial Exemple ": "Editorial Exemple"
}

```

```bash
python3 scripts/process_catalog.py data/catalog_raw.csv data.json --encoding cp1252 --replacements data/replacements.json

```

Replacements are plain, case-sensitive text substitutions applied in file order to **every** CSV field (including EAN, price and schedule), after Unicode normalization. Keep each key specific enough to match only the intended text: a short key such as `"0"` would also change EANs and prices. The file is kept in the repository for reproducible runs, but it is not published on the website (see [What Gets Published](#what-gets-published)).

*(You can also check available options using `python3 scripts/process_catalog.py --help`)*.

*(Alternatively, to generate massive synthetic datasets for performance and scalability testing instead of real data, run:)*

```bash
python3 scripts/generate_catalog.py --books 500 --activities 50 -o data/massive_catalog.csv
python3 scripts/process_catalog.py data/massive_catalog.csv data.json

```

*(You can also check available options using `python3 scripts/generate_catalog.py --help`)*.

4. Compile your CSS changes if necessary (see [Tailwind CSS Local Compilation](#-tailwind-css-local-compilation)).
5. **Bump the versions** (see [Version Management Workflow](#️-version-management-workflow)): `data` if `data.json` changed, `code` if `app.js` or `styles.css` changed.
6. Commit and push `index.html`, `404.html`, `app.js`, `sw.js`, `styles.css`, `src/input.css`, `data.json`, and cover assets (`assets/covers/`) to `main`. The [deploy workflow](#-deployment-github-actions) publishes the site automatically, usually within a couple of minutes.

---

## 🏷️ Version Management Workflow

Versioned URLs (`app.js?v=…`, `styles.css?v=…`, `data.json?v=…`) let browsers and Cloudflare cache files for a week while still picking up every new release. The script `scripts/bump_version.py` keeps those versions in sync in `index.html` and in the Service Worker precache list (`sw.js`), with timezone-aware timestamps (`CET/CEST` via `Europe/Madrid`) and semantic versioning (`MAJOR.MINOR.PATCH`).

### Business Rules

1. **Data updates (`data.json`)**: a new timestamp is written to the `data.json` preload link in `index.html` (`id="dataPreload"`) and to `sw.js`. **`app.js` is not modified**: it reads the data URL and its version from that preload link, so the code version stays the same and devices only download the new data.
2. **Code updates (`app.js` / `styles.css`)**: you choose whether the change is a `patch`, `minor`, or `major` increment. Both files share the same version.
3. **Consistency check**: every run verifies that `index.html` and `sw.js` reference the same versions, and exits with code `1` if they do not or if a file or pattern is missing.
4. **Cover check**: every run also verifies that each cover URL in `data.json` carries the fingerprint of the current cover file (see the covers note in [How to Update the Catalog](#-how-to-update-the-catalog--test-performance)). Outdated or missing covers make it exit with code `1`, which also stops the deployment workflow.

> ⚠️ Never change `app.js` or `styles.css` without bumping the code version, and never edit `?v=` values by hand: versioned files are cached for a week, so a changed file under an unchanged URL would keep being served in its old version.

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

## 🚢 Deployment (GitHub Actions)

The site is published to GitHub Pages by the workflow `.github/workflows/deploy-pages.yml`. Only the files the website needs are published: the rest of the repository (scripts, raw data, sources, documentation) stays in GitHub but is not reachable from the website domain.

### One-time Setup

1. **Settings → Pages → Build and deployment → Source:** `GitHub Actions` (instead of "Deploy from a branch").
2. **Settings → Pages → Custom domain:** keep the custom domain configured there. Deployments made with GitHub Actions take the domain from this setting, so the `CNAME` file does not need to be published. It stays in the repository because the commands of this README read it (`$(cat CNAME)`).

### What Gets Published

The workflow uses an **allowlist**: only these files are copied to the published site.

| Published | Not published |
|---|---|
| `index.html`, `404.html`, `app.js`, `sw.js`, `styles.css`, `data.json`, `assets/` (covers and icons) | `README.md`, `CNAME`, `scripts/`, `data/`, `src/`, `docs/`, `package.json`, `package-lock.json`, `requirements.txt`, ZAP reports and any other file |

If a listed file is missing, the workflow fails instead of publishing an incomplete site. If the website ever needs a new file (e.g. a `manifest.webmanifest`), add it in **two places** of the workflow: the `cp` command of the "Collect site files" step and the `paths` list of the trigger. If it is a JavaScript or HTML file, also add it to the "Minify JS, HTML and JSON" step.

### How It Works

**Triggers:**

* A push to `main` that changes a published file, the workflow itself or the build tools (`package.json` / `package-lock.json`). Pushes that only change the README, the scripts or the raw data do not deploy anything.
* A manual run: **Actions → Deploy to GitHub Pages → Run workflow**.

**Job `build`:**

1. Checks out the repository.
2. Runs `python3 scripts/bump_version.py check`: if `index.html` and `sw.js` reference different versions, the deployment stops and the website keeps its previous version.
3. Installs the build tools with `npm ci` (exact versions and integrity hashes from `package-lock.json`).
4. Copies the allowlisted files to a temporary `_site/` folder, keeping their paths.
5. Minifies the published copies of the JavaScript, HTML and JSON files (see [Minification](#minification)).
6. Lists the published files in the log.
7. Uploads the **contents** of `_site/` as the Pages artifact. They become the root of the website, so every URL stays the same (`_site/assets/covers/x.webp` → `/assets/covers/x.webp`).

**Job `deploy`:** publishes the artifact to the `github-pages` environment.

**Other details:**

* **Least privilege:** the `build` job can only read the repository; only the `deploy` job gets the `pages: write` and `id-token: write` permissions required to publish.
* **One deployment at a time:** a new run waits for the current one, which is never cancelled halfway.
* **No Jekyll processing:** files are published exactly as they are in the repository (publishing from a branch runs them through Jekyll unless a `.nojekyll` file exists).
* **`_site/` is temporary:** it only exists on the GitHub Actions runner. It is ignored in `.gitignore` (`/_site/`) and must never be committed, otherwise the workflow fails when creating it.

### Minification

Only the **published copies** are minified: the repository keeps the readable, commented sources.

| File | Tool | Settings |
|---|---|---|
| `app.js`, `sw.js` | [esbuild](https://esbuild.github.io/) | `--minify` |
| `index.html`, `404.html` | [html-minifier-terser](https://github.com/terser/html-minifier-terser) | `--collapse-whitespace --conservative-collapse --remove-comments` |
| `data.json` | Python `json` | Compact separators (also stops the deployment if the JSON is invalid) |
| `styles.css` | — | Already minified by the Tailwind CLI |
| Covers | — | Already compressed WebP images |

Measured on the first load, after the Brotli compression that Cloudflare applies anyway: about 21 KB → 13 KB transferred for the JS and HTML files (≈ 37 % less). Later visits download nothing, since the Service Worker serves the cached files. Comments are also left out of production.

Guarantees:

* **Safe settings only:** whitespace is collapsed conservatively (single spaces between inline elements are kept), and attributes, quotes and URLs are left untouched, so `id="dataPreload"` and every `?v=` value stay exactly as in the sources.
* **Checks before publishing:** the minified JavaScript is syntax-checked (`node --check`) and the data preload link is verified; any failure stops the deployment.
* **Deterministic output:** the tool versions are pinned with exact versions (`--save-exact`), so the same sources always produce the same bytes. Otherwise a new `sw.js` byte sequence would make every browser install the Service Worker again on each deployment.

Setup (once, then commit `package.json` and `package-lock.json`):

```bash
npm install --save-dev --save-exact esbuild html-minifier-terser

```

> ⚠️ When the minification tools or their settings change (including the first deployment with minification), run `python3 scripts/bump_version.py code`. The published content of `app.js` changes while its source, and therefore its `?v=` URL, does not, so Cloudflare, browsers and Service Workers would keep serving their cached copy for up to a week.

Notes:

* Error messages and stack traces in production refer to the minified code. Reproduce problems locally, where the readable sources are served.
* Local OWASP ZAP scans analyze the readable sources (with comments), while production scans analyze the minified files.

### Verify a Deployment

* **Actions** tab: the run is green. The log of the "List published files" step shows a summary (top-level files with their published size, number of covers, total size) and the full list in the collapsible group "All published files".
* Published and unpublished files:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://$(cat CNAME)/
curl -s -o /dev/null -w "%{http_code}\n" https://$(cat CNAME)/README.md
curl -s -o /dev/null -w "%{http_code}\n" https://$(cat CNAME)/scripts/bump_version.py

```

Expected: `200` for the site, `404` (custom 404 page) for the other two.

### Optional: Purge Cloudflare After Each Deployment

The Cloudflare purge after a deployment is only a safety net (see [Caching](#caching)), but it can be automated by adding this step at the end of the `deploy` job:

```yaml
      - name: Purge Cloudflare cache
        env:
          CF_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CF_ZONE_ID: ${{ secrets.CLOUDFLARE_ZONE_ID }}
        run: |
          curl -fsS -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data '{"purge_everything":true}'
```

It needs two repository secrets (**Settings → Secrets and variables → Actions**):

* `CLOUDFLARE_API_TOKEN`: a Cloudflare API token with only the **Zone → Cache Purge → Purge** permission, limited to this zone.
* `CLOUDFLARE_ZONE_ID`: the zone ID, shown on the domain overview page in Cloudflare.

`purge_everything` empties the cache of the **whole zone** (`genisgrp.xyz`), including any other subdomain.

---

## ☁️ Cloudflare Configuration

The site is served by GitHub Pages behind Cloudflare (custom domain in `CNAME`, proxied by Cloudflare). GitHub Pages does not allow custom response headers, so encryption, security headers and caching are configured in Cloudflare.

### SSL/TLS

**SSL/TLS → Overview → Encryption mode:** `Full (strict)`

Cloudflare connects to GitHub Pages over HTTPS **and** validates its certificate, so the whole path from the visitor to GitHub Pages is encrypted and authenticated:

* `Flexible` would send the requests from Cloudflare to GitHub Pages over plain HTTP. Anyone on that path could read or modify the page, and with **Enforce HTTPS** enabled in GitHub Pages it causes an endless redirect loop.
* `Full` (non-strict) encrypts the connection but accepts any certificate, so it does not prove that Cloudflare is talking to the real GitHub Pages.

**SSL/TLS → Edge Certificates** (connection between visitors and Cloudflare):

| Setting | Value |
|---|---|
| Always Use HTTPS | `On` |
| TLS 1.3 | `On` |
| HTTP Strict Transport Security (HSTS) | `On` · Max-Age: 12 months (`31536000` s) · Include subdomains: `On` · Preload: `Off` |
| Automatic HTTPS Rewrites | `On` |
| Opportunistic Encryption | `On` |

* **Always Use HTTPS:** any `http://` request is redirected to `https://` at the edge, so the page, the data and the Service Worker are always served encrypted. Service Workers only run on HTTPS, so without it a visitor arriving through an `http://` link would get no offline mode.
* **TLS 1.3:** the latest TLS version. It needs fewer round trips to open a connection than TLS 1.2, which noticeably speeds up the first load on high-latency or saturated networks like the one at the fair, and it only allows modern ciphers. Older clients automatically fall back to TLS 1.2.
* **HSTS:** once a browser has visited the site over HTTPS, it refuses to use plain HTTP for it for the next 6 months, even if the user types `http://` or follows an old link. This closes the gap that **Always Use HTTPS** leaves open: the very first unencrypted request, which an attacker on the same Wi-Fi could intercept before the redirect.
  * **Include subdomains** extends the rule to the subdomains of the host that sends it. Cloudflare sends HSTS from every hostname of the zone (`genisgrp.xyz`), so a browser that visits the root domain applies it to **every subdomain of the zone**: any current or future subdomain must work over HTTPS. A browser that only visits this site applies it to `test-festival42.genisgrp.xyz` and its own subdomains.
  * **Preload** is off, so the domain is not hard-coded in browsers: the very first visit of a new browser still relies on the **Always Use HTTPS** redirect. Being on the preload list is hard to undo (removal takes months), so it is only worth enabling for a long-term domain.
  * To disable HSTS, lower **Max-Age** to `0` and keep it like that until visitors' browsers have seen the new value. Browsers that never come back keep the old rule until it expires.
* **Automatic HTTPS Rewrites:** Cloudflare rewrites `http://` links and resources in the HTML to `https://` when they are available over HTTPS, preventing "mixed content" errors. This site only loads its own files with relative URLs and its external links already use `https://`, so it acts as a safety net for future content.
* **Opportunistic Encryption:** lets browsers that request an `http://` URL use an encrypted connection without changing the URL. With **Always Use HTTPS** on, every `http://` request is redirected anyway, so it has practically no effect here. It is kept enabled because it is harmless.

### Security Headers

Three sets of rules work together: custom headers for this app, Cloudflare managed transforms for generic hardening, and a rule that removes a permissive header sent by GitHub Pages.

#### Custom headers

**Rules → Transform Rules → Modify Response Header**, applied to all requests, with **Set static** for each header:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; media-src 'none'; frame-src 'none'; worker-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self';` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Cross-Origin-Embedder-Policy` | `require-corp` |

* **CSP:** only resources of this site can be loaded, which blocks injected scripts, styles or images from other domains. `worker-src 'self'` is required: with `'none'` the Service Worker cannot be registered and the offline mode never starts.
* **COOP:** cuts the link between this tab and windows of other sites (`window.opener`), preventing tabnabbing and cross-site leaks.
* **CORP:** prevents other websites from embedding the covers and files of this site (hotlinking) and keeps them out of other sites' browser processes (Spectre-type attacks). If covers are ever moved to a subdomain or another CDN, those files need `same-site` or `cross-origin` instead.
* **COEP:** the page may only load external resources that explicitly allow it. Today the CSP already blocks every external resource, so it adds little, but it costs nothing. If you ever add one (fonts, analytics, embedded videos…), allow it in the CSP **and** make sure it sends CORP or CORS headers, or it will fail to load.

#### Managed transforms

**Rules → Settings → Managed Transforms** (pre-built rules maintained by Cloudflare, applied to all requests):

* **Remove "X-Powered-By" headers:** `Enabled`. This header reveals the server technology. GitHub Pages does not send it today, but the transform keeps it out if the hosting ever changes, and it is the kind of detail security scanners report.
* **Add security headers:** `Enabled`. It adds these response headers:

| Header | Value | Purpose on this site |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Browsers trust the declared `Content-Type` and never treat a file as a different type (e.g. a JSON or image file run as a script). |
| `X-Frame-Options` | `SAMEORIGIN` | Blocks embedding the page in other sites' frames (clickjacking). It duplicates `frame-ancestors 'self'` of the CSP for older browsers. |
| `Referrer-Policy` | `same-origin` | Links to other sites (festival website, GitHub, LinkedIn…) do not receive the page URL, which can contain the user's search terms (`?search=…`). |
| `X-XSS-Protection` | `1; mode=block` | Legacy header, ignored by current browsers (the CSP provides the real protection). Harmless. |
| `Expect-CT` | `max-age=86400, enforce` | Deprecated and ignored by current browsers, since Certificate Transparency is now always enforced. Harmless. |

#### Remove the CORS wildcard

**Rules → Transform Rules → Modify Response Header**, rule **Remove CORS Wildcard**:

* Expression: `(http.host eq "test-festival42.genisgrp.xyz")`
* Action: **Remove** `access-control-allow-origin`
* Position: after the cache-control rules (see [Caching](#caching)). The order does not change the result, because each rule handles a different header.

GitHub Pages sends `Access-Control-Allow-Origin: *` on every response, which lets any website read the files of this site with `fetch()` (data, catalog, scripts). The app itself only makes same-origin requests, which never need CORS, so removing the header breaks nothing and closes that door. It also clears the "Cross-Domain Misconfiguration" alert reported by OWASP ZAP. If the custom domain ever changes, update the expression.

### WAF

**Security → WAF → Custom rules**, rule **Allow only GET and HEAD**:

* Expression: `(http.host eq "test-festival42.genisgrp.xyz" and not http.request.method in {"GET" "HEAD"})`
* Action: **Block**

The site is static and only needs `GET` (and `HEAD` for header checks such as the `curl -I` commands below), so every other method is rejected at the edge before reaching GitHub Pages. This reduces what can be probed against the site and answers the "Proxy Disclosure" recommendation of OWASP ZAP about `TRACE` and `OPTIONS` (see [Accepted findings](#accepted-findings)). If a form or an API that needs `POST` is ever added, extend the list.

Each method is handled at a different point:

| Method | Answered by | Result |
|---|---|---|
| `GET`, `HEAD` | GitHub Pages | `200` |
| `OPTIONS`, `POST`, `PUT`… | This rule | `403` with the Cloudflare block page |
| `TRACE` | Cloudflare itself, before custom rules run | `405 Not Allowed` (no configuration needed) |

> If the rule seems not to apply, check that no **Skip** custom rule or **IP Access** rule with **Allow** for your IP (e.g. one created for a ZAP scan) is evaluated before it: both make your requests bypass the remaining custom rules.

### Caching

Goal: versioned files and covers are cached for a week, while the app shell (`index.html` and `sw.js`) is always revalidated, so open pages detect a new release within the app update check interval (`UPDATE_CHECK_INTERVAL_MS` in `app.js`, 10 minutes) after GitHub Pages publishes it.

**1. Caching → Configuration → Browser Cache TTL:** `Respect Existing Headers`

By default Cloudflare raises any browser TTL below 4 hours to 4 hours, which could keep an old `index.html` in browsers.

**2. Caching → Cache Rules**, in this order (when several rules match, the last one wins):

| # | Rule | Expression | Settings |
|---|---|---|---|
| 1 | Immutable files | `(http.request.uri.query contains "v=" and not http.request.uri.path in {"/sw.js"}) or http.request.uri.path contains "/assets/covers/"` | Eligible for cache · Edge TTL: ignore cache-control header, 1 week · Browser TTL: override origin, 1 week |
| 2 | Bypass app shell | `http.request.uri.path in {"/" "/index.html" "/sw.js"}` | Bypass cache |

Files without a rule (favicon, error pages) use the 10-minute TTL sent by GitHub Pages.

**3. Rules → Transform Rules → Modify Response Header** (Cache Rules cannot send `no-cache` or `immutable` to browsers):

| Rule | Expression | Header |
|---|---|---|
| App shell | `http.request.uri.path in {"/" "/index.html" "/sw.js"}` | `Cache-Control: no-cache, must-revalidate` |
| Immutable files | Same expression as Cache Rule 1 | `Cache-Control: public, max-age=604800, immutable` |

Browsers follow this `Cache-Control` header, not the Browser TTL of the Cache Rule, so `max-age` must match the intended duration (`604800` seconds = 1 week).

**4. Purge:** run **Caching → Configuration → Purge Everything** once after changing these rules. After that, a purge after each deploy is optional: it only acts as a safety net if a file was changed without bumping its version. It can be automated in the deploy workflow (see [Optional: Purge Cloudflare After Each Deployment](#optional-purge-cloudflare-after-each-deployment)).

### Why this works

* `sw.js` and `index.html` are never cached by Cloudflare, so a new release is visible as soon as GitHub Pages publishes it.
* `app.js?v=…`, `styles.css?v=…` and `data.json?v=…` get a new URL on every change (see [Version Management Workflow](#️-version-management-workflow)), so they can be cached for a week without serving stale content.
* Cover URLs carry a fingerprint of their content (`?v=`, written by `scripts/process_catalog.py`): new books bring new URLs, removed covers are no longer requested (devices delete them on their next visit), and only the covers whose content changes get a new URL.

### Verify the configuration

Encryption:

```bash
curl -sI http://$(cat CNAME)/ | grep -iE "^HTTP|^location"
curl -sI https://$(cat CNAME)/ | grep -i "strict-transport-security"
curl -sv -o /dev/null https://$(cat CNAME)/ 2>&1 | grep -i "SSL connection using"

```

Expected:

* The `http://` request answers with a `301` redirect whose `location` starts with `https://`.
* `strict-transport-security: max-age=31536000; includeSubDomains` (without `preload`).
* The connection uses `TLSv1.3`.

HTTP methods:

```bash
curl -s -o /dev/null -w "GET     %{http_code}\n" https://$(cat CNAME)/
curl -s -o /dev/null -w "OPTIONS %{http_code}\n" -X OPTIONS https://$(cat CNAME)/
curl -s -o /dev/null -w "TRACE   %{http_code}\n" -X TRACE https://$(cat CNAME)/

```

Expected: `GET 200`, `OPTIONS 403`, `TRACE 405`.

Cache headers:

```bash
curl -sI https://$(cat CNAME)/sw.js | grep -iE "cache-control|cf-cache-status"
curl -sI "https://$(cat CNAME)/app.js?v=<current version>" | grep -iE "cache-control|cf-cache-status"

```

Expected:

* `sw.js` and `/`: `cache-control: no-cache, must-revalidate` and `cf-cache-status: BYPASS` or `DYNAMIC`.
* Versioned files and covers: `cache-control: public, max-age=604800, immutable` and `cf-cache-status: HIT` from the second request on.

Security headers:

```bash
curl -sI https://$(cat CNAME)/ | grep -iE "content-security-policy|cross-origin|x-content-type-options|x-frame-options|referrer-policy|x-powered-by|access-control-allow-origin"

```

Expected: the CSP, the three `cross-origin-*` headers, `x-content-type-options`, `x-frame-options` and `referrer-policy` are present, and there is **no** `x-powered-by` nor `access-control-allow-origin`.

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

### Accepted findings

| Alert | ZAP risk | Assessed risk | Reason |
|---|---|---|---|
| Proxy Disclosure | Medium | Info | The detected proxies are Cloudflare and the GitHub Pages CDN: managed services, kept up to date by their providers, publicly visible by design (DNS, footer, this README) and without version numbers. Cloudflare does not allow removing its `server` and `cf-*` headers, so the alert cannot disappear completely. Its recommendations are applied where possible: only `GET` and `HEAD` are allowed (see [WAF](#waf)), `X-Powered-By` is removed, and a custom `404.html` replaces the generic GitHub Pages error page. |

### Custom 404 page

GitHub Pages serves `404.html` (root of the published site) for any missing URL, with a `404` status. It replaces the generic GitHub error page, which identifies the hosting, and offers a link back to the catalog in Catalan. It follows the same security measures as the rest of the site: no scripts, no inline styles (it only uses `styles.css`), and root-relative URLs, so it also works for nested missing paths such as `/a/b/c`. The security headers are added by Cloudflare as for any other response. The Service Worker shows this page as it is: only the app page itself falls back to the cached copy when the network fails.

### 🔒 Security & CSP Compliance
To comply with a strict Content-Security-Policy (CSP) that blocks inline scripts (`unsafe-eval` / inline `<script>` tags), all application logic is completely externalized into `app.js` and loaded securely via the frontend interface. The CSP and the other security headers are set in Cloudflare (see [Security Headers](#security-headers)).

---

## 📄 License

Open-source project distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to fork or adapt for other cultural events or book fairs.
