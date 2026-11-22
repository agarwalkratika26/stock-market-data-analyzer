# GitHub and portfolio checklist

## Prepare the repository

1. Create a new **public** GitHub repository named `stock-market-data-analyzer` (or choose private until ready). Do not include secrets, `.env` files, or virtual environments.
2. Add this project folder to Git. From the project root:

   ```powershell
   git init
   git add .
   git commit -m "Build stock market analyzer dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/stock-market-data-analyzer.git
   git push -u origin main
   ```

3. Replace `YOUR-USERNAME` with your GitHub username. If the folder already has Git history, skip `git init` and inspect the existing remote before adding one.
4. Check the repository page: README image, project description, language mix, setup steps, and license should be visible. Add topics such as `python`, `fastapi`, `nextjs`, `finance`, and `data-visualization`.
5. Make small follow-up commits with meaningful messages, for example `Add RSI alert evaluation` or `Document CSV imports`.

## Suggested repository description

`Educational full-stack market analyzer with FastAPI, pandas indicators, a backtest simulator, and a Next.js dashboard. Includes offline demo data, CSV import, and optional Yahoo Finance history.`

## Portfolio presentation

- Use the dashboard preview in the README, then replace it with a real screenshot after running the app. Capture the browser without personal data and identify whether the displayed provider is demo or public data.
- Add a short project entry to your portfolio: problem, architecture, a few decisions, a limitation, and one next step.
- Link to the README and a short screen recording if you make one. Do not claim a simulated signal or return as a real trade result.
- Add a `CHANGELOG.md` or GitHub Releases when you make meaningful milestones.

## Resume bullet starting point

`Built a full-stack stock market analysis dashboard using Python, FastAPI, pandas, and Next.js; implemented OHLCV ingestion, RSI/MACD/SMA indicators, price alerts, and a cost-aware SMA crossover backtest with next-bar execution.`

Adjust this to match what you can explain and what you personally changed. Do not add impact metrics unless you measured them.

## Before making the repo public

- Confirm `.env`, `.env.local`, `.venv`, `node_modules`, and user-specific files are ignored.
- Include a license and explain that demo prices are synthetic.
- Make setup work from a fresh clone.
- Describe the backtest assumptions and the absence of real-time exchange data.
- Ensure screenshots do not imply synthetic values are actual market prices.
