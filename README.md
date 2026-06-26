# NFL OpenSearch Search & Analytics Layer

A search and analytics layer built on top of a PostgreSQL NFL database using OpenSearch. Enables full-text search across game summaries and aggregation-based analytics, mirroring how production data platforms pair a relational store with a dedicated search engine.

This project is the second half of a two-part NFL data platform:

- **[nfl-postgres-pipeline](https://github.com/SLuckLeonard/nfl-postgres-pipeline)** — PostgreSQL source of truth, ETL pipeline, relational schema
- **nfl-opensearch-layer** ← you are here — search + analytics layer on top of that data

---

## Architecture

```
┌─────────────────────────┐
│   TheSportsDB REST API  │
└────────────┬────────────┘
             │ ingest.py (Project 1)
             ▼
┌─────────────────────────┐
│  PostgreSQL (nfl_stats) │  ← source of truth, relational modeling
│  teams | games | preds  │
└────────────┬────────────┘
             │ index_data.py
             ▼
┌─────────────────────────┐
│ OpenSearch (nfl_games)  │  ← full-text search + aggregation analytics
│    index + mappings     │
└─────────────────────────┘
```

**Why two databases?** PostgreSQL handles transactional writes, foreign key relationships, and is the authoritative record. OpenSearch sits on top as a read-optimized layer — it powers fast full-text search across game summaries and aggregation queries that would be expensive in SQL. 

---

## Index Mapping Design

The `nfl_games` index uses explicit mappings — the OpenSearch equivalent of a schema definition.

| Field | Type | Reason |
|---|---|---|
| `home_team`, `away_team`, `status` | `keyword` | Exact-match filtering (e.g. "Chiefs home games") — not analyzed |
| `game_summary` | `text` | Full-text search with a custom analyzer — tokenized and lowercased |
| `home_score`, `away_score`, `total_points` | `integer` | Range queries and aggregations |
| `over_under_line` | `float` | Decimal precision for betting lines |
| `game_date` | `date` | Date range filtering and sorting |

The custom `nfl_analyzer` uses a standard tokenizer with lowercase and stop-word filters — making searches for "cowboys" match "Dallas Cowboys" regardless of casing.

---

## Project Structure

```
nfl-opensearch-layer/
├── create_index.py     # defines the index mapping in OpenSearch
├── index_data.py       # pulls from PostgreSQL and bulk-indexes into OpenSearch
├── sample_queries.py   # full-text search, filters, aggregations, range queries
├── .env.example        # environment variable template
├── requirements.txt
└── README.md
```

---

## Setup & Usage

### Prerequisites

- Project 1 ([nfl-postgres-pipeline](https://github.com/YOUR_USERNAME/nfl-postgres-pipeline)) must be set up and populated with data
- Docker Desktop installed and running
- Python 3.x

### 1. Start OpenSearch

```bash
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=YourPassword123!" \
  opensearchproject/opensearch:latest
```

Verify it's running (wait ~30 seconds first):
```bash
curl -ku admin:YourPassword123! https://localhost:9200
```

### 2. Install dependencies

```bash
pip install opensearch-py psycopg2-binary python-dotenv
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your PostgreSQL credentials (same values from Project 1):

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nfl_stats
DB_USER=nfl_user
DB_PASS=yourpassword
```

### 4. Run the pipeline

```bash
# Create the index with explicit mappings
python3 create_index.py

# Pull from PostgreSQL and index into OpenSearch
python3 index_data.py

# Run sample search and aggregation queries
python3 sample_queries.py
```

---

## Sample Query Output

### Full-text search: "Cowboys"
```
Dallas Cowboys at Detroit Lions, Week 2 Season 2024. Final score: Detroit Lions 20 - Dallas Cowboys 17.
Baltimore Ravens at Dallas Cowboys, Week 3 Season 2024. Final score: Dallas Cowboys 7 - Baltimore Ravens 28.
```

### Filter: Chiefs home games in 2024
```
Week 2: Kansas City Chiefs vs Buffalo Bills | 34 - 10
Week 4: Kansas City Chiefs vs Miami Dolphins | 24 - 19
```

### Aggregation: Average points scored per home team
```
Buffalo Bills:       31.0 avg pts
Kansas City Chiefs:  29.0 avg pts
Baltimore Ravens:    27.5 avg pts
Detroit Lions:       24.5 avg pts
San Francisco 49ers: 24.0 avg pts
Philadelphia Eagles: 13.0 avg pts
Dallas Cowboys:       7.0 avg pts
```

### Range query: High-scoring games (total > 50 pts)
```
Philadelphia Eagles @ Buffalo Bills:    68 total pts
Detroit Lions @ San Francisco 49ers:    55 total pts
San Francisco 49ers @ Detroit Lions:    53 total pts
```

---

## Index Management

```bash
# Check index health and doc count
curl -ku admin:YourPassword123! https://localhost:9200/_cat/indices?v
curl -ku admin:YourPassword123! https://localhost:9200/nfl_games/_count

# View the full mapping
curl -ku admin:YourPassword123! https://localhost:9200/nfl_games/_mapping

# Check cluster health
curl -ku admin:YourPassword123! https://localhost:9200/_cluster/health?pretty

# Reindex from scratch
curl -ku admin:YourPassword123! -X DELETE https://localhost:9200/nfl_games
python3 create_index.py
python3 index_data.py
```

---

## Tech Stack

- **OpenSearch 2.x** — search engine and analytics store
- **Python** + `opensearch-py` — index creation, bulk ingestion, query execution
- **PostgreSQL** — upstream data source (see Project 1)
- **Docker** — containerized OpenSearch instance
