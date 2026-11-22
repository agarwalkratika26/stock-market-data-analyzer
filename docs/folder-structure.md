# GitHub-ready folder structure

## Python-first course project layout

This layout works well for the intermediate Python/Streamlit version of the project:

```text
Stock-Market-Data-Analyzer/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── src/
│   ├── data_loader.py
│   ├── analysis.py
│   └── visualization.py
├── outputs/
├── images/
├── reports/
├── docs/
├── README.md
├── requirements.txt
├── .gitignore
└── main.py
```

### What each folder is for

- **`data/`** — Input and prepared datasets. `raw/` contains original CSVs; `processed/` holds cleaned files when they need to be saved. Do not commit large, private, licensed, or user-specific datasets without checking permission. Keep synthetic samples clearly labeled.
- **`notebooks/`** — Exploratory Jupyter notebooks. Use them to investigate and prototype; move reusable functions into `src/` rather than leaving all project logic in notebooks.
- **`src/`** — Reusable Python modules for loading, cleaning, analyzing, and visualizing data.
- **`outputs/`** — Generated tables, model results, and exports. Ignore local outputs in Git if they are large or reproducible from code.
- **`images/`** — Screenshots and project figures used in the README or presentation. Label demo data and avoid screenshots containing personal information.
- **`reports/`** — Written analysis reports, such as Markdown or PDF summaries with data source, period, results, and assumptions.
- **`docs/`** — Project architecture, setup guides, methodology, and interview notes.
- **`README.md`** — Project overview, features, setup, data caveats, example output, and usage instructions.
- **`requirements.txt`** — Python package dependencies used by this Python-first version.
- **`.gitignore`** — Excludes virtual environments, secrets, caches, and generated files from Git.
- **`main.py`** — Simple entry point that calls the reusable modules or launches Streamlit.

## How this repository is organized

This workspace implements the advanced full-stack option, so its actual code is separated into `backend/` and `frontend/`. The Python-first layout above is a course-friendly alternative, not an additional set of empty folders to create alongside the current app.

```text
Stock Market Data Analyzer/
├── backend/app/       # Python API, ingestion, analytics, schemas
├── backend/data/      # CSV example and local API state
├── frontend/app/      # Next.js dashboard
├── docs/              # Architecture, walkthrough, plan, interview guide
├── README.md
├── LICENSE
└── .gitignore
```

The mapping is: `backend/app/` contains the reusable source code (the role of `src/`); `backend/data/prices/` contains sample/import data; `frontend/app/` is the dashboard entry point; and `backend/requirements.txt` lists backend Python dependencies. For a compact Python-only course submission, start from the first layout and use a root-level `requirements.txt` and `main.py`.
