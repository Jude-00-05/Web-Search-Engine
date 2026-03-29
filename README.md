# Dataset Search Engine

A full-stack dataset discovery app built inside the existing `Web Search Engine` folder. It aggregates datasets from multiple sources, normalizes them into one schema, builds an inverted index with Python, serves ranked search through a Node API, and presents everything in a polished React interface.

## What It Does

- Searches datasets such as `fresh vs rotten fruits`, `mental health csv`, `image classification datasets`, and `indian traffic dataset`
- Normalizes data from multiple sources into a shared schema
- Builds a field-weighted inverted index
- Serves a REST API from Node.js and Express
- Renders a modern responsive search experience in React

## Architecture

### Data pipeline

- `sources/adapter_huggingface.py`
- `sources/adapter_uci.py`
- `sources/adapter_kaggle.py`
- `sources/adapter_datagov.py`
- `sources/adapter_github.py`
- `scripts/fetch_all.py`
- `scripts/build_index.py`

Python is only used for fetching, normalizing, deduplicating, and indexing data.

### Backend

- `backend/server.js`

The Node API reads `data/merged_datasets.json` and `data/inverted_index.json` directly. It does not call Python during requests.

### Frontend

- `frontend/src/App.js`
- `frontend/src/App.css`

The React app calls the Node API through the CRA development proxy.

## Normalized Dataset Schema

```json
{
  "id": "unique_source_id",
  "title": "Dataset Title",
  "description": "Short description",
  "tags": ["tag1", "tag2"],
  "source": "huggingface",
  "url": "https://...",
  "license": "optional",
  "formats": ["csv", "json"],
  "task_types": ["classification", "nlp"],
  "size": "optional",
  "downloads": 0,
  "last_updated": "YYYY-MM-DD",
  "language": "optional"
}
```

## Search Ranking

The backend uses weighted scoring:

- title match = 3 points
- tags match = 2 points
- task type match = 2 points
- description match = 1 point
- format match = 1 point

It supports multi-word queries and light partial matching by expanding indexed terms that start with the query token.

## API Endpoints

### `GET /api/health`

Returns service health plus dataset and index counts.

### `GET /api/search?q=...`

Returns ranked datasets. Optional filters:

- `sources=huggingface,uci`
- `formats=csv,image`
- `tasks=classification,nlp`

### `GET /api/datasets`

Returns paginated datasets with optional filters.

### `GET /api/sources`

Returns available sources and counts.

## Setup

### 1. Install frontend dependencies

```bash
cd frontend
npm install
```

### 2. Install backend dependencies

```bash
cd backend
npm install
```

### 3. Install Python dependencies

Create a virtual environment if you want, then install:

```bash
pip install nltk huggingface_hub ucimlrepo
```

Optional for future credentialed adapters:

- Kaggle API credentials through `KAGGLE_USERNAME` and `KAGGLE_KEY`
- GitHub token through `GITHUB_TOKEN`

## Build the Dataset Catalog

### Fetch and merge all datasets

```bash
python scripts/fetch_all.py
```

### Build the inverted index

```bash
python scripts/build_index.py
```

The repository already includes a seeded `merged_datasets.json` so the app is usable before live source fetching is configured.

## Run the App

### Start the backend

```bash
cd backend
npm start
```

### Start the frontend

```bash
cd frontend
npm start
```

Open `http://localhost:3000`.

## Notes on Source Adapters

### Hugging Face

Uses `huggingface_hub` when installed. Falls back to seeded datasets if the package or network is unavailable.

### UCI

Uses `ucimlrepo` when installed. Falls back to seeded datasets if needed.

### Kaggle

Scaffolded cleanly with environment-variable support. It currently falls back to seeded entries until credentials are supplied and the official API is wired.

### Data.gov

Uses the public CKAN API when available, with graceful fallback.

### GitHub

Uses the GitHub search API when `GITHUB_TOKEN` is present, with graceful fallback.

## Project Structure

```text
Web Search Engine/
|-- backend/
|   |-- package.json
|   `-- server.js
|-- data/
|   |-- merged_datasets.json
|   |-- inverted_index.json
|   `-- stopwords.txt
|-- frontend/
|   |-- public/
|   |-- src/
|   `-- package.json
|-- scripts/
|   |-- build_index.py
|   `-- fetch_all.py
|-- sources/
|   |-- adapter_datagov.py
|   |-- adapter_github.py
|   |-- adapter_huggingface.py
|   |-- adapter_kaggle.py
|   |-- adapter_uci.py
|   |-- common.py
|   `-- seed_datasets.py
`-- README.md
```

## Future Improvements

- Persist richer per-source metadata
- Add result pagination in the UI
- Add sort controls for relevance, downloads, and freshness
- Expand live source coverage with authenticated Kaggle and GitHub adapters
- Add saved searches and dataset bookmarks
