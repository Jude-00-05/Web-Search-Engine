# Contributing

## Purpose

This repository mixes product code, data pipeline code, and a few legacy experiments. The goal of this guide is to help contributors work in the current product path without wasting time in outdated areas.

## Work In These Areas First

Primary implementation paths:

- `frontend/`
- `backend/`
- `scripts/`
- `sources/`
- `data/`

Legacy or reference-only areas unless explicitly needed:

- `search/`
- `search_engine/`
- `crawler/`

## Local Setup

### Frontend

```bash
cd frontend
npm install
npm start
```

### Backend

```bash
cd backend
npm install
npm start
```

### Python pipeline

```bash
pip install nltk huggingface_hub ucimlrepo
python scripts/rebuild_pipeline.py
```

Optional environment variables are listed in [.env.example](/c:/Projects/Web%20Search%20Engine/.env.example).

## Recommended Development Flow

1. Read [README.md](/c:/Projects/Web%20Search%20Engine/README.md) and [docs/ARCHITECTURE.md](/c:/Projects/Web%20Search%20Engine/docs/ARCHITECTURE.md) before making structural changes.
2. Confirm whether your work targets the active stack or a legacy path.
3. Make the smallest coherent change that solves the problem.
4. If you change pipeline logic, regenerate the impacted artifacts or explain why you did not.
5. If you change API contracts, verify the frontend behavior against those changes.
6. Update docs when behavior, setup, or workflow changes.

## Pull Request Expectations

Good pull requests in this repository should include:

- a clear problem statement
- a concise summary of what changed
- impact on data, API, and UI layers when relevant
- setup or migration notes if contributors need to rerun scripts
- screenshots for frontend changes when possible

## Verification Guidance

There is not yet a full automated verification suite, so use targeted checks:

- frontend smoke test by running the app locally
- backend smoke test through `/api/health` and one search query
- pipeline smoke test by running the specific script you changed
- artifact sanity check by inspecting counts or report outputs in `data/`

If you could not run a check, call that out in your PR.

## Documentation Rule

Update repository docs when you change:

- setup steps
- environment variables
- API behavior
- pipeline scripts
- project structure
- contributor expectations

## Suggested Future Repo Hygiene

- add a license
- add CI for frontend and backend checks
- replace placeholder frontend tests with meaningful coverage
- decide whether legacy directories should be archived or deleted
