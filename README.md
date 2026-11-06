# StatLab

A web app for exploring a dataset two columns at a time. You pick a dataset and
two columns, and it chooses the statistical test that fits those column types,
runs it, and plots the result.

It profiles the columns first, so it knows which are numeric and which work as
groups, and uses that to decide what to run and how to plot it.

![Group comparison](docs/screenshot-group-comparison.png)

## What it runs

| Columns | Analysis | Chart |
|---|---|---|
| numeric + categorical | Kruskal-Wallis | box plot per group |
| categorical + categorical | chi-square test of independence | contingency heatmap |
| numeric + numeric | linear regression | scatter plot with fit line |

Kruskal-Wallis compares groups by rank, so it works without assuming the values
are normally distributed.

A numeric column with 10 or fewer distinct values counts as categorical, so
something like party size in the tips dataset groups properly.

Two datasets are bundled (penguins and tips) and you can upload your own CSV.

| Chi-square | Regression |
|---|---|
| ![Chi-square heatmap](docs/screenshot-chi-square.png) | ![Regression scatter plot](docs/screenshot-regression.png) |

## Components

- `backend/engine.py` - the statistics. Plain functions taking a DataFrame and
  column names, returning dicts. Imports no web code, so the tests run without a
  server.
- `backend/app.py` - FastAPI routes. Resolves which DataFrame a request means,
  calls the engine, returns the result. No statistics here.
- `backend/schemas.py` - Pydantic models for every request and response.
- `frontend/src` - React and TypeScript. `types.ts` mirrors the Pydantic models.
  The components branch on the result's `analysis` field to decide what to render.
- `frontend/src/components` - one view per analysis type, plus the Plotly charts.

Uploaded CSVs are held in memory and disappear when the server restarts.

## Running it

Needs Python 3.11+ and Node 20.19+.

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app is at http://localhost:5173 and the dev server proxies `/api` to the
backend. API docs are at http://localhost:8000/docs.

To run it as one server instead, build the frontend with `npm run build` and
FastAPI will serve `frontend/dist` at http://localhost:8000.

## Tests

```bash
cd backend
pytest
```

31 tests. The engine is tested on synthetic data where the answer is known
(clearly separated groups, identical groups, a known slope) and against published
values for the bundled datasets. The API tests cover the full round trip
including CSV upload.

## Data

The penguins (Gorman, Williams and Fraser 2014) and tips (Bryant and Smith 1995)
datasets are public samples, copied from
[seaborn-data](https://github.com/mwaskom/seaborn-data).
