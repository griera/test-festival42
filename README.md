# 🧪 Test Festival 42 - Static Web Prototype

This repository is a **testing prototype** for a lightweight, serverless catalog and schedule service designed for **Festival 42** (Festival Gèneres Fantàstics de Barcelona). 

It is built as a single-page static web app using **HTML5, Tailwind CSS (via CDN), and Vanilla JavaScript**, prioritizing performance, instant search, and zero maintenance overhead.

---

## 📂 Project Structure

```text
test-festival42/
├── index.html                  # Public frontend interface (search, filters, rendering)
├── data.json                   # Public processed dataset consumed by the web app
├── src/                        # Development source files (not part of the web build)
│   ├── data.csv                # Raw catalog and schedule entries
│   └── convert_csv_to_json.py  # Python script to compile CSV into JSON
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project documentation

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

## 🔄 How to Update the Catalog

1. Edit the raw data in **`src/data.csv`**.
2. Run the conversion script from the root directory to update the JSON payload:
```bash
python3 src/convert_csv_to_json.py

```


3. Commit and push the updated `data.json` and `index.html` to update the GitHub Pages deployment.

---

## 📄 License

Open-source project distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to fork or adapt for other cultural events or book fairs.

