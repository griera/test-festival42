# 🧪 Test Festival 42 - Static Web Prototype

This repository is a **testing prototype** for a lightweight, serverless catalog and schedule service designed for **Festival 42** (Festival Gèneres Fantàstics de Barcelona).

It is built as a single-page static web app using **HTML5, Tailwind CSS (via CDN), and Vanilla JavaScript**, prioritizing performance, instant search, and zero maintenance overhead.

---

## 📂 Project Structure

```text
test-festival42/
├── index.html                # Public frontend interface (search, filters, rendering)
├── data.json                 # Public processed dataset consumed by the web app
├── data/                     # CSV dataset files (raw inputs & processed data)
│   └── catalog.csv
├── scripts/                  # Python development and automation tools
│   ├── generate_large_csv.py # Script for massive synthetic load testing data
│   ├── sanitize_csv.py       # Script to clean, fix encoding (cp1252), and normalize raw CSVs
│   └── csv_to_json.py        # Script to compile CSV into JSON
├── .gitignore                # Git exclusion rules
└── README.md                 # Project documentation

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

---

## 🔄 How to Update the Catalog & Test Performance

1. Place your raw semicolon-delimited CSV source file (exported from booksellers, typically in legacy `cp1252` encoding) inside your workspace.
2. **Sanitize the raw CSV:** Clean text, fix encoding, normalize Unicode, and map headers using the preprocessing script:

```bash
python3 scripts/sanitize_csv.py path/to/raw_booksellers_data.csv data/catalog.csv --encoding cp1252

```

*(Optional: You can pass `--replacements replacements.json` to handle specific recurring source typos).*

*(You can also check available options using `python3 scripts/sanitize_csv.py --help`)*.

*(Alternatively, to generate massive synthetic datasets for performance and scalability testing instead of real data, run:)*

```bash
python3 scripts/generate_large_csv.py --books 500 --talks 20 --signings 30 -o data/catalog.csv

```

3. Run the conversion script from the root directory to compile the clean CSV into the public JSON payload:

```bash
python3 scripts/convert_csv_to_json.py --input data/catalog.csv --output data.json

```

*(You can check available input/output arguments by running `python3 scripts/convert_csv_to_json.py --help`).*

4. Commit and push the updated `data.json` and frontend files (`index.html`) to deploy changes via GitHub Pages.

---

## 🛡️ Security Audit

This static prototype is audited locally using **OWASP ZAP** via Docker.

### Prerequisites

* Docker
* Local server running (`python3 -m http.server 8000`)

### Run local scan

```bash
docker run --rm -v $(pwd):/zap/wrk/:rw -t --add-host=host.docker.internal:host-gateway ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://host.docker.internal:8000 -J zap_report.json -r zap_report.html

```

---

## 📄 License

Open-source project distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to fork or adapt for other cultural events or book fairs.
