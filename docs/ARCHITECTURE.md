# Architecture

## System Overview

The project follows a generated-data architecture:

1. Python fetchers collect dataset metadata from external providers.
2. Validation and deduplication reduce noisy or invalid records.
3. A generated inverted index supports fast local search.
4. A Node.js API serves catalog and search endpoints from flat JSON files.
5. A React frontend provides the user-facing search experience.
6. Live Deep Search optionally queries external providers in real time.

## Main Components

### Source adapters

Location: `sources/`

Responsibilities:

- fetch raw dataset metadata
- normalize source-specific fields into a shared schema
- provide resilient fallbacks when network or package access is limited

Current adapters:

- `adapter_huggingface.py`
- `adapter_uci.py`
- `adapter_kaggle.py`
- `adapter_datagov.py`
- `adapter_github.py`

### Validation layer

Key files:

- `sources/validation.py`
- `sources/common.py`

Responsibilities:

- normalize dataset records
- reject weak titles, weak descriptions, and invalid URLs
- enforce source-aware quality rules
- prevent low-signal GitHub repositories from polluting the catalog

### Pipeline scripts

Location: `scripts/`

Key scripts:

- `fetch_all.py`
- `validate_datasets.py`
- `check_links.py`
- `build_index.py`
- `rebuild_pipeline.py`

Responsibilities:

- orchestrate source fetching
- create merged dataset artifacts
- validate and prune bad entries
- verify dataset destination URLs
- generate the inverted index and reports

### Data artifacts

Location: `data/`

Important files:

- `merged_datasets.json`
- `inverted_index.json`
- `fetch_report.json`
- `validation_report.json`
- `link_check_report.json`
- `index_report.json`

The backend treats these files as its local read model.

### Backend API

Location: `backend/server.js`

Responsibilities:

- load and refresh catalog/index data
- tokenize and rank indexed search queries
- support filters for source, format, and task type
- expose summary and discovery endpoints
- proxy live deep-search behavior through `liveSearch.js`

### Live Deep Search

Location: `backend/liveSearch.js`

Responsibilities:

- run live source queries in parallel
- normalize live responses into the same broad result shape
- score and deduplicate results
- cache recent live queries for a short period

This path favors freshness and breadth over the stricter quality controls used in the local indexed catalog.

### Frontend

Location: `frontend/src/`

Responsibilities:

- capture user queries
- submit indexed and deep-search requests
- render filters and result cards
- surface loading, empty, and failure states

## Search Model

The local indexed search uses:

- weighted field scoring
- phrase boosts
- partial term expansion through prefix matching
- source weighting
- query intent adjustments for specific patterns

This makes the backend more opinionated than a simple inverted-index lookup while still avoiding a separate search engine dependency.

## Canonical Dataset Schema

The normalized catalog uses a shared schema similar to:

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

## Active Stack vs Legacy Stack

Current product path:

- `frontend/`
- `backend/`
- `sources/`
- `scripts/`
- `data/`

Legacy or prototype paths:

- `search/`
- `search_engine/`
- `crawler/`

These older areas are useful for historical reference but should not be treated as the default extension point for new work.

## Architecture Strengths

- simple local development model
- no database required for core search
- deterministic generated artifacts
- easy-to-understand separation between ingestion and serving

## Architecture Risks

- generated JSON artifacts can drift from source reality
- no formal deployment or CI pipeline is defined
- backend and pipeline logic are coupled through shared file conventions
- some source integrations depend on external availability and credentials
