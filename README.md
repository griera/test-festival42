# 🧪 Test Festival 42 - Static Web Prototype

This repository is a **testing prototype** for a lightweight, serverless catalog and schedule service designed for **Festival 42** (Festival Gèneres Fantàstics de Barcelona).

It is built as a single-page static web app using **HTML5, Tailwind CSS (via CDN), and Vanilla JavaScript**, prioritizing performance, instant search, and zero maintenance overhead.

---

## 📂 Project Structure

```text
test-festival42/
├── index.html                # Public frontend interface (search, filters, rendering)
├── data.json                 # Public processed dataset consumed by the web app
├── data/                     # Raw CSV input files (catalog & schedule entries)
│   └── catalog.csv
├── scripts/                  # Python development and automation tools
│   ├── generate_large_csv.py # Script for massive synthetic load testing data
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

1. Edit or add your semicolon-delimited CSV source data inside the **`data/`** directory.
2. To generate massive synthetic datasets for performance and scalability testing, run the generation script with custom parameters:

```bash
python3 scripts/generate_large_csv.py --books 500 --talks 20 --signings 30 -o data/catalog.csv

```

*(You can also check available options using `python3 scripts/generate_large_csv.py --help`)*.

3. Run the conversion script from the root directory to compile the CSV into the public JSON payload:

```bash
python3 scripts/convert_csv_to_json.py --input data/catalog.csv --output data.json

```

*(You can check available input/output arguments by running `python3 scripts/convert_csv_to_json.py --help`).*

4. Commit and push the updated `data.json` and `index.html` to deploy changes via GitHub Pages.

---

## 📄 License

Open-source project distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to fork or adapt for other cultural events or book fairs.
