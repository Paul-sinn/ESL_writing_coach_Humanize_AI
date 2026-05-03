# Humanize AI Detector

English-language AI detector and paid humanizer built with `FastAPI`, `LangGraph`, and a `React + Vite` frontend.

## Features

- Free `Basic Analysis`
- Paid `Advanced Analysis` at `50 credits`
- Paid `Humanize Essay` at `250 credits`
- Free `Basic Analysis` is limited to `2 runs per day per IP`; the 3rd attempt is blocked and routed to upgrade/billing
- `1200 words` input limit with visible live counter in the UI
- Separate `Humanize Requirements` section for constraints like `Keep it above 500 words`
- Billing panel with `$10/month Pro`, `$5` credits, and `$10` credits
- LangGraph orchestration for analysis and rewrite flows

## Project Structure

- `backend/app/main.py`: FastAPI API entrypoint
- `backend/app/graphs.py`: LangGraph workflows and node logic
- `backend/app/services/`: billing, analysis, and humanize services
- `frontend/`: React + Vite client
- `tests/`: lightweight backend tests

## Run

1. Install Python dependencies from `pyproject.toml`
2. Install frontend dependencies in `frontend/`
3. Run the API server:

```bash
uvicorn main:app --reload
```

4. Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

If you build the frontend into `frontend/dist`, FastAPI will also serve the compiled app.

## Demo Billing States

Use the `X-User-Id` header to simulate different billing states during API testing.

- `demo-free`: free account with `0` credits
- `demo-pro`: pro account with `840` credits
