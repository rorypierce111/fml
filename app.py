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
# DATABASE FUNCTIONS
# -----------------------------
def get_cities():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM cities;")
            rows = cur.fetchall()

    return [r[0] for r in rows]


# -----------------------------
# WEATHER API FUNCTION
# -----------------------------
def get_weather(city):
    if not WEATHER_API_KEY:
        return {"city": city, "error": "WEATHER_API_KEY not set"}

    try:
        r = requests.get(
            WEATHER_URL,
            params={
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            },
            timeout=5
        )

        data = r.json()

        if r.status_code != 200:
            return {"city": city, "error": data}

        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "conditions": data["weather"][0]["description"]
        }

    except requests.RequestException as e:
        return {"city": city, "error": str(e)}


# -----------------------------
# ROUTES
# -----------------------------

# 🚀 Lightweight root route (DO NOT TOUCH DB HERE)
@app.route("/")
def index():
    return "App running"


# Actual dashboard route
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
        results = [get_weather(city) for city in cities]

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Railway health endpoint
@app.route("/health")
def health():
    try:
        # Minimal DB check
        with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
            pass

        return {"status": "ok"}

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
