# { "Depends": "py-genlayer:test" }

# ═══════════════════════════════════════════════════════════
#  GenLayer Weather Oracle — Tools & Infrastructure
#  Live weather data for any city, fully on-chain.
#  Uses Open-Meteo API — no API key required.
#
#  DEVELOPER QUICKSTART:
#  ┌─────────────────────────────────────────────────────┐
#  │  get_weather("Lagos")              → fetch + cache  │
#  │  get_multiple(["Lagos","London"])  → batch fetch    │
#  │  get_forecast("Lagos", 3)          → 3-day forecast │
#  │  get_weather_alert("Lagos")        → danger check   │
#  │  compare_cities("Lagos","London")  → side by side   │
#  │  get_hottest()                     → hottest city   │
#  │  get_coldest()                     → coldest city   │
#  │  get_humidity_alert(90)            → high humidity  │
#  │  get_wind_alert(50)                → high winds     │
#  │  get_weather_summary()             → AI briefing    │
#  │  get_cached("Lagos")               → free read      │
#  │  get_all()                         → all cached     │
#  │  list_cities()                     → supported list │
#  └─────────────────────────────────────────────────────┘
# ═══════════════════════════════════════════════════════════

from genlayer import *
import json
import typing


CITIES = {
    "London":        ("51.5074", "-0.1278"),
    "New York":      ("40.7128", "-74.0060"),
    "Lagos":         ("6.5244",  "3.3792"),
    "Tokyo":         ("35.6762", "139.6503"),
    "Paris":         ("48.8566", "2.3522"),
    "Dubai":         ("25.2048", "55.2708"),
    "Singapore":     ("1.3521",  "103.8198"),
    "Nairobi":       ("1.2921",  "36.8219"),
    "Port Harcourt": ("4.8156",  "7.0498"),
    "Abuja":         ("9.0765",  "7.3986"),
    "Berlin":        ("52.5200", "13.4050"),
    "Sydney":        ("-33.8688","151.2093"),
    "Toronto":       ("43.6532", "-79.3832"),
}


def fetch_current(city: str, lat: str, lon: str) -> str:
    """Helper that fetches current weather and handles API errors gracefully."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,"
            f"wind_speed_10m,precipitation,weathercode"
            f"&timezone=auto"
        )
        raw = gl.nondet.web.render(url, mode="text")

        if not raw or raw.strip() in ["null", "", "null\n"]:
            return json.dumps({
                "error": "Open-Meteo API is down. Please try again later.",
                "status": "unavailable"
            })

        data = json.loads(raw)

        if "current" not in data:
            return json.dumps({
                "error": "Open-Meteo API is down. Please try again later.",
                "status": "unavailable"
            })

        current = data["current"]
        result = {
            "city":        city,
            "temperature": current["temperature_2m"],
            "humidity":    current["relative_humidity_2m"],
            "wind_speed":  current["wind_speed_10m"],
            "rain":        current["precipitation"],
            "weathercode": current["weathercode"],
            "unit":        data["current_units"]["temperature_2m"],
            "status":      "ok",
        }
        return json.dumps(result, sort_keys=True)

    except Exception:
        return json.dumps({
            "error": "Open-Meteo API is down. Please try again later.",
            "status": "unavailable"
        })


class WeatherOracle(gl.Contract):

    cache: str

    def __init__(self):
        self.cache = "{}"

    # ── CORE FETCH METHODS ─────────────────────────────────

    @gl.public.write
    def get_weather(self, city: str) -> typing.Any:
        """Fetch live weather for one city and cache it on-chain."""
        coords = CITIES.get(city)
        if not coords:
            all_weather = json.loads(self.cache)
            all_weather[city] = {"error": f"{city} is not a supported city.", "status": "unsupported"}
            self.cache = json.dumps(all_weather, sort_keys=True)
            return

        lat, lon = coords

        def fetch() -> str:
            return fetch_current(city, lat, lon)

        fresh = gl.eq_principle.prompt_comparative(
            fetch,
            "The outputs represent weather data for the same city. "
            "They are equivalent if both show an API down error, "
            "or if temperature is within 1 degree, humidity within 5%, "
            "and wind speed within 3 km/h of each other."
        )

        all_weather = json.loads(self.cache)
        all_weather[city] = json.loads(fresh)
        self.cache = json.dumps(all_weather, sort_keys=True)

    @gl.public.write
    def get_multiple(self, cities: list) -> typing.Any:
        """Fetch live weather for multiple cities in one transaction."""
        all_weather = json.loads(self.cache)

        for city in cities:
            coords = CITIES.get(city)
            if not coords:
                all_weather[city] = {"error": f"{city} is not a supported city.", "status": "unsupported"}
                continue

            lat, lon = coords

            def fetch() -> str:
                return fetch_current(city, lat, lon)

            fresh = gl.eq_principle.prompt_comparative(
                fetch,
                "The outputs represent weather data for the same city. "
                "They are equivalent if both show an API down error, "
                "or if temperature is within 1 degree, humidity within 5%, "
                "and wind speed within 3 km/h of each other."
            )
            all_weather[city] = json.loads(fresh)

        self.cache = json.dumps(all_weather, sort_keys=True)

    @gl.public.write
    def get_forecast(self, city: str, days: int) -> typing.Any:
        """Fetch a multi-day forecast for a city. days: 1 to 7."""
        coords = CITIES.get(city)
        if not coords:
            return

        lat, lon = coords
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,weathercode,wind_speed_10m_max"
            f"&timezone=auto"
            f"&forecast_days={days}"
        )

        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url, mode="text")

                if not raw or raw.strip() in ["null", "", "null\n"]:
                    return json.dumps({
                        "error": "Open-Meteo API is down. Please try again later.",
                        "status": "unavailable"
                    })

                data = json.loads(raw)

                if "daily" not in data:
                    return json.dumps({
                        "error": "Open-Meteo API is down. Please try again later.",
                        "status": "unavailable"
                    })

                daily = data["daily"]
                forecast = []
                for i in range(len(daily["time"])):
                    forecast.append({
                        "date":        daily["time"][i],
                        "temp_max":    daily["temperature_2m_max"][i],
                        "temp_min":    daily["temperature_2m_min"][i],
                        "rain_total":  daily["precipitation_sum"][i],
                        "wind_max":    daily["wind_speed_10m_max"][i],
                        "weathercode": daily["weathercode"][i],
                    })
                return json.dumps({
                    "city":     city,
                    "days":     days,
                    "status":   "ok",
                    "forecast": forecast,
                }, sort_keys=True)

            except Exception:
                return json.dumps({
                    "error": "Open-Meteo API is down. Please try again later.",
                    "status": "unavailable"
                })

        fresh = gl.eq_principle.prompt_comparative(
            fetch,
            "The outputs represent a weather forecast for the same city. "
            "They are equivalent if both show an API down error, "
            "or if temperatures are within 2 degrees and dates match exactly."
        )

        all_weather = json.loads(self.cache)
        if city not in all_weather:
            all_weather[city] = {}
        all_weather[city]["forecast"] = json.loads(fresh)
        self.cache = json.dumps(all_weather, sort_keys=True)

    @gl.public.write
    def get_weather_alert(self, city: str) -> typing.Any:
        """Uses LLM to analyze cached weather and flag dangerous conditions."""
        all_weather = json.loads(self.cache)

        if city not in all_weather:
            return

        weather = all_weather[city]

        if weather.get("status") == "unavailable":
            all_weather[city]["alert"] = {
                "error": "Cannot generate alert — weather data unavailable.",
                "status": "unavailable"
            }
            self.cache = json.dumps(all_weather, sort_keys=True)
            return

        def analyze() -> str:
            prompt = (
                f"Analyze this weather data for {city} and determine if conditions "
                f"are dangerous:\n\n{json.dumps(weather)}\n\n"
                f"Consider: temperature extremes, high winds above 60 km/h, "
                f"heavy rain above 10mm, severe weathercodes (95-99).\n\n"
                f"Respond ONLY with JSON in this exact format:\n"
                f'{{"city": "{city}", '
                f'"alert_level": "safe" or "caution" or "danger", '
                f'"reason": "one sentence explanation", '
                f'"recommendation": "one sentence advice for residents"}}'
            )
            return gl.nondet.exec_prompt(prompt)

        alert = gl.eq_principle.prompt_comparative(
            analyze,
            "Both outputs assess the same weather conditions for the same city. "
            "They are equivalent if they assign the same alert level."
        )

        all_weather[city]["alert"] = json.loads(alert)
        self.cache = json.dumps(all_weather, sort_keys=True)

    @gl.public.write
    def get_weather_summary(self) -> typing.Any:
        """Uses LLM to generate a global weather briefing from all cached cities."""
        all_weather = json.loads(self.cache)
        if not all_weather:
            return

        def summarize() -> str:
            prompt = (
                f"You are a professional meteorologist. Based on this weather data "
                f"from cities around the world, write a concise two-sentence global "
                f"weather briefing:\n\n{json.dumps(all_weather)}\n\n"
                f"Respond with only the briefing, nothing else."
            )
            return gl.nondet.exec_prompt(prompt)

        summary = gl.eq_principle.prompt_comparative(
            summarize,
            "Both outputs summarize the same global weather conditions. "
            "They are equivalent if they mention the same key trends."
        )

        all_weather["summary"] = summary
        self.cache = json.dumps(all_weather, sort_keys=True)

    @gl.public.write
    def compare_cities(self, city1: str, city2: str) -> typing.Any:
        """Uses LLM to generate a side-by-side comparison of two cached cities."""
        all_weather = json.loads(self.cache)

        if city1 not in all_weather or city2 not in all_weather:
            return

        w1 = all_weather[city1]
        w2 = all_weather[city2]

        if w1.get("status") == "unavailable" or w2.get("status") == "unavailable":
            return

        def analyze() -> str:
            prompt = (
                f"Compare the weather conditions of {city1} and {city2}:\n\n"
                f"{city1}: {json.dumps(w1)}\n"
                f"{city2}: {json.dumps(w2)}\n\n"
                f"Respond ONLY with JSON in this exact format:\n"
                f'{{"city1": "{city1}", '
                f'"city2": "{city2}", '
                f'"warmer": "the warmer city name", '
                f'"more_humid": "the more humid city name", '
                f'"windier": "the windier city name", '
                f'"summary": "one sentence comparison"}}'
            )
            return gl.nondet.exec_prompt(prompt)

        comparison = gl.eq_principle.prompt_comparative(
            analyze,
            "Both outputs compare the same two cities. "
            "They are equivalent if they identify the same warmer and windier city."
        )

        all_weather[f"{city1}_vs_{city2}"] = json.loads(comparison)
        self.cache = json.dumps(all_weather, sort_keys=True)

    # ── FREE READ METHODS ──────────────────────────────────

    @gl.public.view
    def get_cached(self, city: str) -> str:
        """Returns last cached weather for a city. Free — no transaction needed."""
        all_weather = json.loads(self.cache)
        if city in all_weather:
            return json.dumps(all_weather[city])
        return json.dumps({"error": f"{city} not cached. Call get_weather first."})

    @gl.public.view
    def get_all(self) -> str:
        """Returns all cached weather data. Free — no transaction needed."""
        return self.cache

    @gl.public.view
    def list_cities(self) -> str:
        """Returns all cities supported by this oracle."""
        return json.dumps(list(CITIES.keys()))

    @gl.public.view
    def get_hottest(self) -> str:
        """Returns the hottest city currently in cache."""
        all_weather = json.loads(self.cache)
        cities = {
            k: v for k, v in all_weather.items()
            if isinstance(v, dict) and "temperature" in v and v.get("status") == "ok"
        }
        if not cities:
            return json.dumps({"error": "No valid weather data cached yet."})
        hottest = max(cities.items(), key=lambda x: x[1]["temperature"])
        return json.dumps({"city": hottest[0], "data": hottest[1]})

    @gl.public.view
    def get_coldest(self) -> str:
        """Returns the coldest city currently in cache."""
        all_weather = json.loads(self.cache)
        cities = {
            k: v for k, v in all_weather.items()
            if isinstance(v, dict) and "temperature" in v and v.get("status") == "ok"
        }
        if not cities:
            return json.dumps({"error": "No valid weather data cached yet."})
        coldest = min(cities.items(), key=lambda x: x[1]["temperature"])
        return json.dumps({"city": coldest[0], "data": coldest[1]})

    @gl.public.view
    def get_humidity_alert(self, threshold: int) -> str:
        """Returns all cities with humidity above the given threshold (%)."""
        all_weather = json.loads(self.cache)
        alerts = []
        for city, data in all_weather.items():
            if isinstance(data, dict) and "humidity" in data and data.get("status") == "ok":
                if data["humidity"] >= threshold:
                    alerts.append({
                        "city":        city,
                        "humidity":    data["humidity"],
                        "temperature": data.get("temperature"),
                    })
        if not alerts:
            return json.dumps({"message": f"No cities above {threshold}% humidity."})
        alerts.sort(key=lambda x: x["humidity"], reverse=True)
        return json.dumps({"threshold": threshold, "cities": alerts})

    @gl.public.view
    def get_wind_alert(self, threshold: int) -> str:
        """Returns all cities with wind speed above the given threshold (km/h)."""
        all_weather = json.loads(self.cache)
        alerts = []
        for city, data in all_weather.items():
            if isinstance(data, dict) and "wind_speed" in data and data.get("status") == "ok":
                if data["wind_speed"] >= threshold:
                    alerts.append({
                        "city":       city,
                        "wind_speed": data["wind_speed"],
                        "temperature": data.get("temperature"),
                    })
        if not alerts:
            return json.dumps({"message": f"No cities above {threshold} km/h wind speed."})
        alerts.sort(key=lambda x: x["wind_speed"], reverse=True)
        return json.dumps({"threshold": threshold, "cities": alerts})