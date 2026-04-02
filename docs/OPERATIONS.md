# Operations

## Operating Model

This project is maintained as a file-backed search application. Operational work usually means one of three things:

- refresh the dataset catalog
- rebuild search artifacts
- verify the app still serves correct results

## Environment Variables

See [.env.example](/c:/Projects/Web%20Search%20Engine/.env.example).

Supported variables today:

- `PORT`
- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `GITHUB_TOKEN`

## Core Commands

### Run the API

```bash
cd backend
npm start
```

### Run the frontend

```bash
cd frontend
npm start
```

### Rebuild everything

```bash
python scripts/rebuild_pipeline.py
```

## Pipeline Runbook

### Fetch datasets

```bash
python scripts/fetch_all.py
```

Expected outputs:

- `data/merged_datasets.json`
- `data/fetch_report.json`

### Validate datasets

```bash
python scripts/validate_datasets.py
```

Expected outputs:

- updated `data/merged_datasets.json`
- `data/validation_report.json`

### Check links

```bash
python scripts/check_links.py
```

Expected outputs:

- updated `data/merged_datasets.json`
- `data/link_check_report.json`

### Build index

```bash
python scripts/build_index.py
```

Expected outputs:

- `data/inverted_index.json`
- `data/index_report.json`

## Smoke Test Checklist

After a rebuild or backend change:

1. Start the backend and check `GET /api/health`.
2. Run a sample indexed query with `GET /api/search?q=mental health csv`.
3. Open the frontend and confirm results render.
4. Trigger Deep Search once and confirm the UI handles success or failure cleanly.
5. Inspect generated report files in `data/` for obviously unexpected drops.

## Common Failure Modes

### External source failures

Symptoms:

- fewer fetched datasets than expected
- adapter-specific errors during rebuilds
- Deep Search source failures

Likely causes:

- third-party API downtime
- changed upstream response shapes
- missing credentials
- network restrictions

### Weak result quality

Symptoms:

- generic datasets surfacing too high
- empty or thin search results
- too many low-signal GitHub entries

Likely areas to inspect:

- `backend/server.js`
- `backend/liveSearch.js`
- `sources/validation.py`
- adapter normalization logic in `sources/`

### Stale search behavior

Symptoms:

- backend returns outdated catalog results
- frontend does not reflect rebuilt artifacts

Actions:

1. rerun the relevant pipeline scripts
2. call `POST /api/reload`
3. restart the backend if needed

## Maintenance Priorities

- keep adapter behavior aligned with upstream providers
- tighten validation as new noisy data patterns appear
- maintain documentation whenever setup or workflow changes
- decide on the long-term fate of legacy directories

## Suggested Next Ops Improvements

- add CI for linting, smoke tests, and script validation
- version generated artifacts more intentionally
- add monitoring if the backend is deployed
- define a regular catalog refresh cadence
