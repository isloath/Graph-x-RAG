# Graph RAG — Loan Fraud Detection Platform

Production-ready local-first fraud analytics platform that combines graph analytics, deterministic risk scoring, semantic retrieval, and grounded RAG.

## Capabilities
- Graph model for applications and identifiers (`Phone`, `Email`, `Document`, `Device`, `Account`, `Wallet`) with tolerant missing identifier ingestion.
- Incremental ingestion into Memgraph and vector indexing in Qdrant.
- Baseline deterministic risk scoring:
  - Shared phone (>=2): +20
  - Shared document (>=2): +40
  - Shared device (>=3): +25
  - High-degree identifier (>=5): +30
  - Louvain cluster size >=5: +35
- Community detection via Memgraph MAGE Louvain, persisted to `Application.community_id`.
- RAG pipeline:
  - semantic search (top-k default 5)
  - graph expansion up to 2 hops
  - grounded answer generation with local Mistral (Ollama)
  - evidence references included in response

## Architecture
- **API:** FastAPI (async endpoints)
- **Graph:** Memgraph + MAGE procedures
- **Vector DB:** Qdrant
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Local LLM:** Ollama Mistral

## Quickstart

```bash
docker compose up --build -d
```

Pull mistral model once Ollama is running:

```bash
docker exec -it ollama ollama pull mistral
```

Run sample data generation:

```bash
python scripts/generate_sample_data.py -n 5000 -o data/sample_applications.json
```

Ingest sample data:

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H 'Content-Type: application/json' \
  -d @data/sample_applications.json
```


## Local investigation workflow (no web UI)
1. Start stack: `docker compose up --build -d`
2. Ingest data via API/CLI (use `scripts/ingest_chunked.py` for large files).
3. Recompute communities: `POST /api/v1/communities/recompute`.
4. Visualize graph directly in Memgraph Lab at `http://localhost:7444` (query `MATCH p=(a:Application)-[*1..2]-(n) RETURN p LIMIT 200`).
5. Ask LLM-grounded questions through `POST /api/v1/rag-query` (uses local Ollama).

## API Endpoints
- `POST /api/v1/ingest`
- `GET /api/v1/applications?page=1&page_size=50`
- `GET /api/v1/applications/{application_id}`
- `GET /api/v1/applications/{application_id}/graph`
- `POST /api/v1/risk/{application_id}`
- `POST /api/v1/communities/recompute`
- `GET /api/v1/fraud-rings`
- `GET /api/v1/semantic-search?q=shared+document&top_k=5`
- `POST /api/v1/rag-query`
- `POST /api/v1/reset`

## Example investigation queries
- "Which applications appear connected to the same document and device?"
- "Show likely fraud rings over size 5 with highest repeated identifiers."
- "Why was application APP-0001201 flagged as high risk?"
- "Find clusters where loan amounts are high and phone numbers are reused."

## Performance and scaling notes
- Designed for incremental ingestion and single-node deployment.
- Add batching in ingest clients for target >5k apps/sec.
- Tune Memgraph memory and Qdrant storage for 5M applications / 50M edges.
- CPU-only execution is supported; GPU is optional for embeddings/LLM acceleration.

## Testing

```bash
pip install -e .[dev]
pytest -q
```

## Project layout
```
app/
  api/
  core/
  repositories/
  services/
  models/
scripts/
tests/
```

## Chunked ingestion helper

```bash
python scripts/ingest_chunked.py data/sample_applications.json --base-url http://localhost:8000 --chunk-size 500
```

If you previously hit `500` on `/api/v1/ingest`:
- ensure Memgraph is reachable (graph ingestion is mandatory),
- ensure Qdrant/Ollama are up for full RAG features,
- this project now degrades gracefully when vector indexing is temporarily unavailable (graph ingest still succeeds).
