import json
import os
import requests

# ---------------------------
# CONFIGURATION
# ---------------------------
BASE_URL = os.environ.get("BASE_URL", "https://v1.basketball.api-sports.io")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def resp(status, body):
    """Standardized JSON response formatter"""
    try:
        body_str = json.dumps(body, default=str)
    except Exception as e:
        body_str = json.dumps({"error": f"Failed to serialize response: {str(e)}"})

    response = {
        "statusCode": int(status),
        "headers": CORS_HEADERS,
        "body": body_str
    }

    print("📤 Lambda returning response:", json.dumps(response)[:500])
    return response


def rq(path, params=None):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "v1.basketball.api-sports.io"
    }

    full_url = f"{BASE_URL}{path}"
    print("🔍 Calling:", full_url, "with", params)

    try:
        r = requests.get(full_url, headers=headers, params=params or {}, timeout=15)
        print("🟢 Status:", r.status_code)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        print("❌ Error fetching from API:", str(e))
        return None, str(e)


def normalize_season(s):
    """Ensure season format is 'YYYY-YYYY'."""
    if not s:
        return "2023-2024"
    s = str(s).strip()
    if "-" in s:
        return s
    return f"{s}-{int(s) + 1}"


# ---------------------------
# HELPERS
# ---------------------------
def find_player_id(name):
    if not name:
        return None, []
    name = name.strip()
    lower_name = name.lower()
    words = lower_name.split()
    first = words[0] if len(words) > 1 else ""
    last = words[-1]
    params = {"search": last}
    data, err = rq("/players", params)
    if err or not data:
        return None, []
    players = data.get("response", [])
    if not players:
        return None, []
    for p in players:
        pname = p.get("name", "").lower()
        if pname == lower_name or pname == f"{last} {first}" or pname == f"{first} {last}":
            return p["id"], players
    for p in players:
        pname = p.get("name", "").lower()
        if last in pname and first in pname:
            return p["id"], players
    usa_guards = [p for p in players if p.get("country") == "USA" and p.get("position") == "Guard"]
    if usa_guards:
        return usa_guards[0]["id"], players
    usa_players = [p for p in players if p.get("country") == "USA"]
    if usa_players:
        return usa_players[0]["id"], players
    return players[0]["id"], players


def find_team_id(name):
    if not name:
        return None
    data, err = rq("/teams", {"search": name})
    if err or not data:
        return None
    teams = data.get("response", [])
    if not teams:
        return None
    for t in teams:
        if name.lower() in t.get("name", "").lower():
            return t["id"]
    return teams[0]["id"]


def find_team_id_by_name(team_name, season=None):
    if not team_name:
        return None
    search_term = team_name.strip().lower()
    parts = search_term.split()

    known_map = {
        "atlanta hawks": 132,
        "boston celtics": 133,
        "brooklyn nets": 134,
        "charlotte hornets": 135,
        "chicago bulls": 136,
        "cleveland cavaliers": 137,
        "dallas mavericks": 138,
        "denver nuggets": 139,
        "detroit pistons": 140,
        "golden state warriors": 141,
        "houston rockets": 142,
        "indiana pacers": 143,
        "los angeles clippers": 144,
        "los angeles lakers": 145,
        "memphis grizzlies": 146,
        "miami heat": 147,
        "milwaukee bucks": 148,
        "minnesota timberwolves": 149,
        "new orleans pelicans": 150,
        "new york knicks": 151,
        "oklahoma city thunder": 152,
        "orlando magic": 153,
        "philadelphia 76ers": 154,
        "phoenix suns": 155,
        "portland trail blazers": 156,
        "sacramento kings": 157,
        "san antonio spurs": 158,
        "team giannis": 1411,
        "team lebron": 1412,
        "toronto raptors": 159,
        "utah jazz": 160,
        "washington wizards": 161
    }

    # Check direct map first
    for key, tid in known_map.items():
        if key in search_term:
            return tid

    search_terms = [search_term]
    if len(parts) > 1:
        search_terms.extend([parts[-1], parts[0]])

    for term in search_terms:
        params = {"league": 12, "search": term}
        if season:
            params["season"] = season
        data, err = rq("/teams", params)
        if err or not data:
            continue
        items = data.get("response", [])
        if not items:
            continue
        for item in items:
            team = item.get("team") or {}
            league = item.get("league") or {}
            if str(league.get("id")) != "12":
                continue
            name_fields = [
                str(team.get("name") or "").lower(),
                str(team.get("nickname") or "").lower(),
                str(team.get("city") or "").lower(),
                str(team.get("code") or "").lower()
            ]
            if any(x in search_term or search_term in x for x in name_fields):
                return team.get("id")

    for key, tid in known_map.items():
        if any(k in search_term for k in key.split()):
            return tid

    return None


# ---------------------------
# ROUTES
# ---------------------------
def handle_player_stats(q):
    player_name = q.get("player")
    season = normalize_season(q.get("season"))
    pid, candidates = find_player_id(player_name)
    if not pid:
        return resp(404, {"error": "Player not found", "query": q})
    data, err = rq("/games/statistics/players", {"player": pid, "season": season})
    if err or not data or not data.get("response"):
        return resp(404, {"error": "No stats found", "query": q, "player_id": pid})
    stats = data["response"]
    return resp(200, {"query": q, "player_id": pid, "total_games": len(stats), "data": stats})


def handle_team_stats(q):
    season = normalize_season(q.get("season"))
    team_name = q.get("team")
    if not team_name:
        return resp(400, {"error": "Provide a team name"})
    team_id = find_team_id_by_name(team_name, season)
    if not team_id:
        return resp(404, {"error": f"Team '{team_name}' not found"})
    params = {"league": 12, "season": season, "team": team_id}
    data, err = rq("/statistics", params)
    if err or not data or not data.get("response"):
        return resp(404, {"error": "No stats found", "query": q, "team_id": team_id})
    return resp(200, {"query": q, "team_id": team_id, "data": data["response"]})


def handle_standings(q):
    season = normalize_season(q.get("season"))
    params = {"league": 12, "season": season}
    data, err = rq("/standings", params)
    if err or not data or not data.get("response"):
        return resp(404, {"error": "No standings found", "query": q})
    standings = data["response"]
    if isinstance(standings, list) and "league" in standings[0]:
        standings = standings[0]["league"]["standings"]
    return resp(200, {"query": q, "standings": standings})


def handle_games(q):
    team_name = q.get("team")
    season = normalize_season(q.get("season"))
    tid = find_team_id_by_name(team_name, season) if team_name else None
    params = {"league": 12, "season": season}
    if tid:
        params["team"] = tid
    data, err = rq("/games", params)
    if err or not data or not data.get("response"):
        return resp(404, {"error": "No games found", "query": q, "team_id": tid})
    return resp(200, {"query": q, "team_id": tid, "games": data["response"]})


def handle_team_roster(q):
    team_name = q.get("team")
    season = normalize_season(q.get("season"))
    tid = find_team_id_by_name(team_name, season)
    if not tid:
        return resp(404, {"error": "Team not found", "query": q})
    params = {"team": tid, "season": season}
    data, err = rq("/players", params)
    if err or not data or not data.get("response"):
        return resp(404, {
            "error": "No players found for team",
            "query": q,
            "team_id": tid,
            "api_params": params
        })
    return resp(200, {
        "query": q,
        "team_id": tid,
        "season": season,
        "roster": data["response"]
    })


def handle_h2h(q):
    season = normalize_season(q.get("season"))
    team1 = q.get("team1")
    team2 = q.get("team2")
    if not team1 or not team2:
        return resp(400, {"error": "Provide both team1 and team2 names"})
    t1_id = find_team_id_by_name(team1, season)
    t2_id = find_team_id_by_name(team2, season)
    if not t1_id or not t2_id:
        return resp(404, {"error": "Invalid team(s)", "team1_id": t1_id, "team2_id": t2_id})
    h2h_param = f"{min(t1_id, t2_id)}-{max(t1_id, t2_id)}"
    params = {"h2h": h2h_param, "league": 12, "season": season}
    print(f"🔍 Fetching H2H data for {team1} vs {team2}: {params}")
    data, err = rq("/games", params)
    if (not data or not data.get("response")) and t1_id > t2_id:
        alt_h2h = f"{t2_id}-{t1_id}"
        params["h2h"] = alt_h2h
        print(f"🔁 Retrying reversed H2H: {alt_h2h}")
        data, err = rq("/games", params)
    if err or not data or not data.get("response"):
        return resp(404, {
            "error": "No head-to-head data found",
            "teams": [team1, team2],
            "params": params
        })
    return resp(200, {
        "query": q,
        "teams": [team1, team2],
        "h2h": params["h2h"],
        "total_games": len(data["response"]),
        "data": data["response"]
    })


# ---------------------------
# MAIN LAMBDA HANDLER
# ---------------------------
def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event, indent=2))
    path = (
        event.get("rawPath")
        or event.get("path")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or "/"
    ).lower().rstrip("/")
    print("Resolved path:", path)
    q = event.get("queryStringParameters") or {}
    if not RAPIDAPI_KEY:
        return resp(500, {"error": "Missing RAPIDAPI_KEY"})
    if path.endswith("/nba/player-stats"):
        return handle_player_stats(q)
    elif path.endswith("/nba/team-stats"):
        return handle_team_stats(q)
    elif path.endswith("/nba/standings"):
        return handle_standings(q)
    elif path.endswith("/nba/games"):
        return handle_games(q)
    elif path.endswith("/nba/team-roster"):
        return handle_team_roster(q)
    elif path.endswith("/nba/h2h"):
        return handle_h2h(q)
    else:
        return resp(404, {"error": "Unknown route", "path": path})


print("✅ RAPIDAPI_KEY loaded:", bool(RAPIDAPI_KEY))


def generate_team_id_map():
    data, err = rq("/teams", {"league": 12})
    if err or not data:
        print("❌ Error fetching teams:", err)
        return
    teams = data.get("response", [])
    for t in teams:
        team = t.get("team", {})
        print(f'"{team["name"].lower()}": {team["id"]},')
