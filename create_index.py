from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", "YourPassword123!"),
    use_ssl=True,
    verify_certs=False
)

index_name = "nfl_games"

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "nfl_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "game_id":        {"type": "integer"},
            "season":         {"type": "integer"},
            "week":           {"type": "integer"},
            "home_team":      {"type": "keyword"},
            "away_team":      {"type": "keyword"},
            "home_score":     {"type": "integer"},
            "away_score":     {"type": "integer"},
            "total_points":   {"type": "integer"},
            "over_under_line":{"type": "float"},
            "game_date":      {"type": "date"},
            "game_summary":   {"type": "text", "analyzer": "nfl_analyzer"},
            "status":         {"type": "keyword"}
        }
    }
}

if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)

client.indices.create(index=index_name, body=mapping)
print(f"Index '{index_name}' created.")