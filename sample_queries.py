from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", "YourPassword123!"),
    use_ssl=True, verify_certs=False
)

# ── 1. Full-text search across game summaries ──────────────────────────────
print("\n── Full-text search: 'Cowboys' ──")
results = client.search(index="nfl_games", body={
    "query": {"match": {"game_summary": "Cowboys"}},
    "size": 5
})
for hit in results["hits"]["hits"]:
    print(hit["_source"]["game_summary"])

# ── 2. Filter by team + season ─────────────────────────────────────────────
print("\n── Filter: Chiefs home games in 2024 ──")
results = client.search(index="nfl_games", body={
    "query": {
        "bool": {
            "must": [
                {"term": {"home_team": "Kansas City Chiefs"}},
                {"term": {"season": 2024}}
            ]
        }
    }
})
for hit in results["hits"]["hits"]:
    s = hit["_source"]
    print(f"Week {s['week']}: {s['home_team']} vs {s['away_team']} | {s.get('home_score')} - {s.get('away_score')}")

# ── 3. Aggregation: avg points scored per team ─────────────────────────────
print("\n── Aggregation: Avg points per home team ──")
results = client.search(index="nfl_games", body={
    "size": 0,
    "aggs": {
        "by_team": {
            "terms": {"field": "home_team", "size": 32},
            "aggs": {
                "avg_points": {"avg": {"field": "home_score"}}
            }
        }
    }
})
for bucket in results["aggregations"]["by_team"]["buckets"]:
    print(f"{bucket['key']}: {bucket['avg_points']['value']:.1f} avg pts")

# ── 4. Range query: high-scoring games ────────────────────────────────────
print("\n── High-scoring games (total > 50 pts) ──")
results = client.search(index="nfl_games", body={
    "query": {
        "range": {"total_points": {"gt": 50}}
    },
    "sort": [{"total_points": "desc"}],
    "size": 5
})
for hit in results["hits"]["hits"]:
    s = hit["_source"]
    print(f"{s['away_team']} @ {s['home_team']}: {s['total_points']} total pts")