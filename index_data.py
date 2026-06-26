import os, psycopg2
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

load_dotenv()

pg = psycopg2.connect(
    host=os.getenv("DB_HOST"), dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
)
cur = pg.cursor()

os_client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", "YourPassword123!"),
    use_ssl=True, verify_certs=False
)

cur.execute("""
    SELECT g.game_id, g.season, g.week,
           ht.name AS home_team, at.name AS away_team,
           g.home_score, g.away_score, g.total_points,
           g.over_under_line, g.game_date, g.status
    FROM games g
    JOIN teams ht ON ht.team_id = g.home_team_id
    JOIN teams at ON at.team_id = g.away_team_id
""")

rows = cur.fetchall()
cols = [d[0] for d in cur.description]

def generate_docs(rows, cols):
    for row in rows:
        doc = dict(zip(cols, row))
        # Create a human-readable summary for full-text search
        doc["game_summary"] = (
            f"{doc['away_team']} at {doc['home_team']}, "
            f"Week {doc['week']} Season {doc['season']}. "
            f"Final score: {doc['home_team']} {doc.get('home_score', 'TBD')} - "
            f"{doc['away_team']} {doc.get('away_score', 'TBD')}."
        )
        if doc.get("game_date"):
            doc["game_date"] = str(doc["game_date"])
        yield {"_index": "nfl_games", "_id": doc["game_id"], "_source": doc}

success, failed = helpers.bulk(os_client, generate_docs(rows, cols))
print(f"Indexed {success} docs, {failed} failures.")

cur.close()
pg.close()