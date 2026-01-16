import json
import os
import re
import urllib.parse
import urllib.request

import boto3

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "").rstrip("/")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-haiku-20240307-v1:0"
)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
}


def make_resp(status, body):
    """Standard HTTP+JSON response with CORS and safe serialization."""
    try:
        body_str = json.dumps(body, default=str)
    except Exception as e:
        body_str = json.dumps({"error": f"Failed to serialize response: {str(e)}"})

    resp = {
        "statusCode": int(status),
        "headers": CORS_HEADERS,
        "body": body_str,
    }
    print("📤 Lambda response (truncated):", json.dumps(resp)[:800])
    return resp


# ----------------------------------------------------
# Bedrock helpers
# ----------------------------------------------------
def call_bedrock_text(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """
    Call Claude 3 Haiku (Bedrock messages API) and return plain text.
    Uses low temperature for deterministic, stable behavior.
    """
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "top_p": 1.0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}],
            }
        ],
    }

    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(payload).encode("utf-8"),
        )
        body = json.loads(response["body"].read())
        texts = [c["text"] for c in body.get("content", []) if c.get("type") == "text"]
        return "".join(texts).strip()
    except Exception as e:
        print("🔥 Error calling Bedrock:", str(e))
        # Fallback text so Lambda still returns something
        return "I'm sorry, I had trouble generating a response from the AI model."


def call_bedrock_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Ask Claude to return ONLY JSON. If parsing fails, try to salvage JSON snippet.
    """
    assistant_output = call_bedrock_text(system_prompt, user_prompt, max_tokens=400)
    try:
        return json.loads(assistant_output)
    except Exception:
        try:
            start = assistant_output.index("{")
            end = assistant_output.rindex("}") + 1
            return json.loads(assistant_output[start:end])
        except Exception:
            print("⚠️ Failed to parse JSON from Bedrock output:", assistant_output[:400])
            return {}


# ----------------------------------------------------
# Backend helpers (call your API Gateway)
# ----------------------------------------------------
def backend_get(path: str, params: dict | None = None) -> dict:
    """
    Call the backend API and return either parsed JSON or an error dict.
    """
    if not BACKEND_BASE_URL:
        return {"error": "BACKEND_BASE_URL not set"}

    base = BACKEND_BASE_URL.rstrip("/")
    url = f"{base}{path}"

    qs = urllib.parse.urlencode(params or {})
    full_url = f"{url}?{qs}" if qs else url

    print("🔍 Calling backend URL:", full_url)

    try:
        with urllib.request.urlopen(full_url, timeout=15) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="ignore")

        print("🔍 Backend status:", status)
        if status != 200:
            return {
                "error": f"Backend returned HTTP {status}",
                "body": raw,
            }

        return json.loads(raw)

    except Exception as e:
        print("🔥 Error calling backend:", str(e))
        return {"error": f"Error calling backend: {str(e)}"}


def call_backend_player_stats(player_name: str, season: str | None) -> dict:
    params = {"player": player_name}
    if season:
        params["season"] = season
    return backend_get("/nba/player-stats", params)


def call_backend_team_stats(team_name: str, season: str | None) -> dict:
    params = {"team": team_name}
    if season:
        params["season"] = season
    return backend_get("/nba/team-stats", params)


def call_backend_standings(season: str | None) -> dict:
    params = {}
    if season:
        params["season"] = season
    return backend_get("/nba/standings", params)


def call_backend_games(team_name: str | None, season: str | None) -> dict:
    params = {}
    if team_name:
        params["team"] = team_name
    if season:
        params["season"] = season
    return backend_get("/nba/games", params)


def call_backend_team_roster(team_name: str, season: str | None) -> dict:
    params = {"team": team_name}
    if season:
        params["season"] = season
    return backend_get("/nba/team-roster", params)


def call_backend_h2h(team1: str, team2: str, season: str | None) -> dict:
    params = {"team1": team1, "team2": team2}
    if season:
        params["season"] = season
    return backend_get("/nba/h2h", params)


# ----------------------------------------------------
# Intent + entity extraction helpers
# ----------------------------------------------------
TEAM_ABBREV_MAP = {
    "okc": "Oklahoma City Thunder",
    "thunder": "Oklahoma City Thunder",
    "lal": "Los Angeles Lakers",
    "lakers": "Los Angeles Lakers",
    "gsw": "Golden State Warriors",
    "warriors": "Golden State Warriors",
    "bos": "Boston Celtics",
    "celtics": "Boston Celtics",
    # extend as needed
}


def infer_season_from_text(text: str) -> str | None:
    """
    Try to infer NBA season string from free text.
    - "2022 season"        -> "2021-2022"
    - "2023-24" / "2023/24" -> "2023-2024"
    - bare "2022"          -> "2021-2022" (typical NBA usage)
    """
    if not text:
        return None

    # patterns like 2023-24 or 2023/24
    m = re.search(r"(20\d{2})\s*[-/]\s*(\d{2})", text)
    if m:
        start = int(m.group(1))
        end_suffix = int(m.group(2))
        end = (start // 100) * 100 + end_suffix
        return f"{start}-{end}"

    # single year like "2022"
    m = re.search(r"(20\d{2})", text)
    if m:
        year = int(m.group(1))
        if 1950 < year < 2100:
            return f"{year-1}-{year}"

    return None


def normalize_team_name(name: str | None) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    return TEAM_ABBREV_MAP.get(key, name)


INTENT_SYSTEM_PROMPT = """
You are an assistant that extracts structured JSON commands for an NBA stats chatbot.

Return ONLY valid JSON with this structure:

{
  "intent": "player_stats | team_stats | standings | games | team_roster | h2h | chit_chat",
  "player_name": null or string,
  "team_name": null or string,
  "team1": null or string,
  "team2": null or string,
  "season": null or string
}

Important NBA rules:
- NBA seasons span 2 calendar years. If the user says "2022 season"
  that usually means the 2021-2022 season. Represent it as "2021-2022".
- If the user says "2023-24" or "2023/24", normalize to "2023-2024".
- Team abbreviations like "OKC" or "LAL" should be expanded to their full team
  names, e.g. "Oklahoma City Thunder", "Los Angeles Lakers".

Intents:
- If the user asks about a specific player, use "player_stats" and set "player_name".
- If they ask about a specific team's performance, record, wins/losses, or stats, use "team_stats".
- If they ask for standings, rankings, seeds, or who is first/last in the conference, use "standings".
- If they ask about games, schedule, or results, use "games".
- If they ask "who is on X", "X roster", "players on X", use "team_roster".
- If they ask how two teams compare head-to-head, use "h2h" and set "team1" and "team2".
- If it's general chat that cannot be answered from stats, use "chit_chat".

Examples (you MUST follow these):
User: "Give me Nikola Jokic's stats for 2022 season"
-> {
  "intent": "player_stats",
  "player_name": "Nikola Jokic",
  "team_name": null,
  "team1": null,
  "team2": null,
  "season": "2021-2022"
}

User: "Who is on the OKC roster?"
-> {
  "intent": "team_roster",
  "player_name": null,
  "team_name": "Oklahoma City Thunder",
  "team1": null,
  "team2": null,
  "season": null
}

User: "How do the Lakers and Celtics compare head to head?"
-> {
  "intent": "h2h",
  "player_name": null,
  "team_name": null,
  "team1": "Los Angeles Lakers",
  "team2": "Boston Celtics",
  "season": null
}

Return ONLY JSON. No explanations, no extra keys.
""".strip()


def extract_intent_and_entities(user_message: str) -> dict:
    """
    Use Bedrock to extract intent + entities, then clean them up with heuristics.
    """
    user_prompt = f"User question:\n{user_message}\n\nReturn the JSON command."
    result = call_bedrock_json(INTENT_SYSTEM_PROMPT, user_prompt) or {}

    intent = result.get("intent") or "chit_chat"
    player_name = result.get("player_name")
    team_name = normalize_team_name(result.get("team_name"))
    team1 = normalize_team_name(result.get("team1"))
    team2 = normalize_team_name(result.get("team2"))
    season = result.get("season")

    # Fallback season inference from raw text if Bedrock didn't set it
    if not season:
        season = infer_season_from_text(user_message)

    lm = user_message.lower()

    # Heuristic fixes when intent came back as chit_chat
    if intent == "chit_chat":
        if "roster" in lm or "who is on" in lm or "lineup" in lm:
            intent = "team_roster"
        elif "stats" in lm or "averages" in lm or "box score" in lm:
            if player_name:
                intent = "player_stats"
            elif team_name:
                intent = "team_stats"

    return {
        "intent": intent,
        "player_name": player_name,
        "team_name": team_name,
        "team1": team1,
        "team2": team2,
        "season": season,
    }


# ----------------------------------------------------
# Final answer generation
# ----------------------------------------------------
ANSWER_SYSTEM_PROMPT = """
You are an NBA analytics assistant. You receive:
- The user's question,
- A high-level 'intent' indicating what they asked for,
- Structured JSON data from a stats backend (if available).

Your rules:

1. You MUST treat the backend JSON as the only source of numeric stats
   (points per game, rebounds, assists, shooting percentages, totals, etc.).
2. If the backend JSON has an "error" field or is missing the requested data,
   you MUST NOT guess or invent any specific numbers.
   In that case:
   - Briefly explain that the stats could not be retrieved,
   - You may give a very high-level qualitative answer
     (e.g., "an MVP-level season"), but do NOT state concrete stats.
3. If the backend JSON looks valid, summarize the most relevant numbers
   (averages, totals, key trends) in clear, conversational English.
4. Do NOT dump raw JSON or long game lists unless the user explicitly asks.
5. Be concise: 1–3 short paragraphs plus bullet points if helpful.
""".strip()


def build_answer(user_message: str, intent: str, entities: dict, backend_data: dict) -> str:
    """
    Build the final natural-language answer using backend JSON + Bedrock.
    """
    context = {
        "intent": intent,
        "entities": entities,
        "backend": backend_data,
    }

    user_prompt = (
        "User question:\n"
        f"{user_message}\n\n"
        "Structured context from backend (JSON):\n"
        f"{json.dumps(context, default=str)[:8000]}\n\n"
        "Now write the best possible answer for the user, using ONLY this data "
        "for numeric stats."
    )

    return call_bedrock_text(ANSWER_SYSTEM_PROMPT, user_prompt, max_tokens=650)


# ----------------------------------------------------
# Lambda handler
# ----------------------------------------------------
def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event)[:4000])

    # OPTIONS -> CORS preflight
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or "GET"
    ).upper()

    if method == "OPTIONS":
        return make_resp(200, {"ok": True})

    # Extract user message from JSON body or query string
    body = event.get("body")
    if isinstance(body, str):
        try:
            body_json = json.loads(body)
        except Exception:
            body_json = {}
    else:
        body_json = body or {}

    message = body_json.get("message")

    if not message:
        qs = event.get("queryStringParameters") or {}
        message = qs.get("message") or qs.get("q")

    if not message:
        return make_resp(400, {"error": "No message provided"})

    # Step 1: intent & entity extraction
    entities = extract_intent_and_entities(message)
    intent = entities["intent"]
    debug = dict(entities)  # shallow copy for debug

    print("🔎 Parsed intent/entities:", json.dumps(entities))

    # Step 2: call appropriate backend endpoint
    backend_data: dict

    if intent == "player_stats" and entities.get("player_name"):
        backend_data = call_backend_player_stats(
            entities["player_name"], entities.get("season")
        )

    elif intent == "team_stats" and entities.get("team_name"):
        backend_data = call_backend_team_stats(
            entities["team_name"], entities.get("season")
        )

    elif intent == "standings":
        backend_data = call_backend_standings(entities.get("season"))

    elif intent == "games":
        backend_data = call_backend_games(
            entities.get("team_name"), entities.get("season")
        )

    elif intent == "team_roster" and entities.get("team_name"):
        backend_data = call_backend_team_roster(
            entities["team_name"], entities.get("season")
        )

    elif intent == "h2h" and entities.get("team1") and entities.get("team2"):
        backend_data = call_backend_h2h(
            entities["team1"], entities["team2"], entities.get("season")
        )

    else:
        backend_data = {
            "note": "No backend call made for this intent or missing entities."
        }

    debug["backend"] = backend_data

    # Step 3: build final answer via Bedrock
    answer = build_answer(message, intent, entities, backend_data)

    return make_resp(
        200,
        {
            "answer": answer,
            "intent": intent,
            "debug": debug,  # keep this for troubleshooting in the UI
        },
    )
