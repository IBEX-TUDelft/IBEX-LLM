curl -X POST "http://localhost:10341/spawn-agents" \
-H "Content-Type: application/json" \
-d '{
    "username": "jasper",
    "password": "dteMpzfEnS7B8fX3nph3smy54bZffRVS",
    "players": 3,
    "hostname": "188.166.34.67",
    "game_params": "game.json"
}'