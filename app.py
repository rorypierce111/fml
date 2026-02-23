import os
import requests
import psycopg
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


# -----------------------------
# DATABASE HELPERS
# -----------------------------
def get_conn():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")
    return psycopg.connect(DATABASE_URL, sslmode="require")


def get_cities():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM cities;")
            rows = cur.fetchall()
    return [r[0] for r in rows]


# -----------------------------
# WEATHER API FUNCTION
# -----------------------------
def get_weather(city: str):
    if not WEATHER_API_KEY:
        return {"city": city, "error": "WEATHER_API_KEY not set"}

    try:
        r = requests.get(
            WEATHER_URL,
            params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=5,
        )
        data = r.json()

        if r.status_code != 200:
            return {"city": city, "error": data}

        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "conditions": data["weather"][0]["description"],
        }

    except requests.RequestException as e:
        return {"city": city, "error": str(e)}


# -----------------------------
# ROUTES
# -----------------------------

# Liveness: MUST be fast and never depend on DB/external APIs
@app.route("/")
def index():
    return "App running", 200


@app.route("/dashboard")
def dashboard():
    try:
        cities = get_cities()
        initial_weather = get_weather(cities[0]) if cities else None

        return render_template(
            "index.html",
            cities=cities,
            initial_weather=initial_weather,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/weather")
def weather_json():
    try:
        city = request.args.get("city")

        if city:
            return jsonify(get_weather(city))

        cities = get_cities()

        # Optional safety cap to avoid hammering the API if the table grows
        # cities = cities[:20]

        results = [get_weather(c) for c in cities]
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Railway health endpoint: keep this as liveness (no DB)
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


# Readiness endpoint: checks DB connectivity (optional for your own monitoring)
@app.route("/ready")
def ready():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "unready", "error": str(e)}), 500


if __name__ == "__main__":
    # Only used when running locally with `python app.py`
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=False)