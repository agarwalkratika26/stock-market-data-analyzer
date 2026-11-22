# Installation guide

## Python setup

Use Python 3.11 or newer for this project. Check that Python and pip are available before creating a virtual environment:

```text
python --version
python -m pip --version
```

On some Windows installations, use `py` instead of `python`. Install Python from the official Python website if it is missing; on Windows, enable the option to add Python to PATH during installation.

## Libraries

For the recommended Python analysis / Streamlit version, the core packages are:

- `pandas` and `numpy` — data tables and numeric calculations
- `matplotlib` and `seaborn` — static charts and exploratory visualizations
- `yfinance` — optional public historical data retrieval
- `streamlit` — optional interactive Python dashboard
- `datetime` — included with Python; no separate pip install is needed
- `plotly` — optional interactive charts

For the full-stack version in this repository, install `backend/requirements.txt`. It includes FastAPI, Uvicorn, pandas, NumPy, yfinance, and Pydantic Settings. The browser dashboard is a separate Next.js project and requires Node.js and npm; see the README quick start.

## Virtual environment

A virtual environment keeps this project's Python dependencies separate from other Python projects. Create one from the project folder, activate it, then install packages. Activate the environment again whenever you open a new terminal to work on the project.

### Windows PowerShell — current full-stack backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

If PowerShell blocks environment activation, either use Command Prompt activation (`.venv\Scripts\activate.bat`) in Command Prompt or run the Python executable directly as `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### macOS / Linux — current full-stack backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python run.py
```

### Python-only analysis / Streamlit option

Create and activate the virtual environment from the project root using the matching Windows or macOS command above. For a Python-first course project with a root `requirements.txt`, install the analysis packages with:

```text
python -m pip install pandas numpy matplotlib seaborn yfinance streamlit
```

Optional Plotly charts can be installed with `python -m pip install plotly`. If you use a checked-in requirements file, put the chosen packages there so another person can recreate the environment.

## Frontend setup for this repository

Keep the backend running, then open a second terminal at the repository root:

```text
cd frontend
npm install
```

Copy `frontend/.env.example` to `.env.local`, then start the dashboard:

```text
npm run dev
```

Open `http://localhost:3000`. The FastAPI documentation is at `http://127.0.0.1:8000/docs`.

## Common installation issues

- **`python` not found:** try `py` on Windows or `python3` on macOS/Linux; confirm Python is installed and available in PATH.
- **Wrong environment:** activate `.venv` before installing and running Python packages.
- **Permission error:** avoid global `pip` installs; use the project virtual environment.
- **CSV works but Yahoo does not:** `yfinance` requires an internet connection and public provider data may be unavailable. Use the CSV/demo source as a fallback.
- **Dashboard cannot reach the API:** start the backend first and confirm it is listening on port 8000; then start the Next.js app on port 3000.
