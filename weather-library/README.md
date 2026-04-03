# GenLayer Weather Oracle

On-chain weather intelligence. Not just a data feed — a full atmospheric decision layer for your Intelligent Contracts.

Built on GenLayer using Open-Meteo. No API key. No setup. Deploy and go.

---

## Why This Is Different

Most on-chain weather tools stop at fetching a temperature. This contract goes further. It analyzes conditions, flags danger, compares cities, generates forecasts, and produces an AI-written global weather briefing — all verified by five independent validators before anything touches the chain.

It is not a wrapper. It is infrastructure.

---

## API

**Open-Meteo**
`https://api.open-meteo.com/v1/forecast`

- Free and open source
- No API key required
- Coordinate-based queries for city-level precision
- Powered by high-resolution numerical weather prediction models
- Returns current conditions and multi-day forecasts

> **Accuracy Notice:** Open-Meteo is a numerical forecast model, not a physical sensor network. Readings may vary ±1–2°C from ground-level conditions depending on local terrain and microclimate. This oracle is suitable for atmospheric monitoring, contract triggers, and weather-dependent logic — not for precision scientific instrumentation.

---

## What Makes It Stand Out

### Multi-Day Forecast On-Chain
```
get_forecast("Lagos", 3)
```
Returns daily max temperature, min temperature, total rainfall, max wind speed and weathercode for each day. First weather oracle on GenLayer to support forecasting.

### AI Danger Alerts
```
get_weather_alert("Port Harcourt")
```
The LLM analyzes cached conditions and returns one of three alert levels — `safe`, `caution`, or `danger` — with a plain-English reason and a recommendation for residents. No hardcoded thresholds. The AI interprets context.

### City-vs-City Comparison
```
compare_cities("Lagos", "London")
```
Returns which city is warmer, more humid, and windier — plus a one-sentence summary. Useful for logistics, agriculture, and event planning contracts.

### Global Weather Briefing
```
get_weather_summary()
```
After caching multiple cities, the LLM writes a two-sentence global weather briefing like a professional meteorologist. Fully on-chain. Consensus-verified.

### Threshold Alerts
```
get_humidity_alert(90)   → all cities above 90% humidity
get_wind_alert(50)       → all cities above 50 km/h wind
```
Filter your entire cache by condition threshold in one free call. No transaction needed.

### Hottest and Coldest
```
get_hottest()   → warmest city in cache
get_coldest()   → coolest city in cache
```

---

## Full Method Reference

### Write (requires a transaction)

| Method | Description |
|---|---|
| `get_weather(city)` | Fetch current conditions for one city |
| `get_multiple(cities)` | Fetch multiple cities in one transaction |
| `get_forecast(city, days)` | Fetch 1–7 day forecast |
| `get_weather_alert(city)` | AI danger assessment |
| `compare_cities(city1, city2)` | AI side-by-side comparison |
| `get_weather_summary()` | AI global weather briefing |

### Read (free — no transaction)

| Method | Description |
|---|---|
| `get_cached(city)` | Last cached data for one city |
| `get_all()` | Everything cached at once |
| `list_cities()` | All supported cities |
| `get_hottest()` | Warmest city in cache |
| `get_coldest()` | Coldest city in cache |
| `get_humidity_alert(threshold)` | Cities above humidity % |
| `get_wind_alert(threshold)` | Cities above wind speed |

---

## Supported Cities

London, New York, Lagos, Tokyo, Paris, Dubai, Singapore, Nairobi, Port Harcourt, Abuja, Berlin, Sydney, Toronto.

More cities can be added by contributing coordinates to the `CITIES` dictionary in the contract.

---

## WMO Weather Codes

| Code | Condition |
|---|---|
| 0 | Clear sky |
| 1 – 3 | Partly cloudy |
| 45 – 48 | Fog |
| 51 – 67 | Rain |
| 71 – 77 | Snow |
| 80 – 82 | Rain showers |
| 95 – 99 | Thunderstorm |

---

## Quick Start

```
1. Paste contract.py into GenLayer Studio
2. Deploy — no constructor arguments needed
3. Call get_multiple(["Lagos", "London", "Dubai"])
4. Call get_forecast("Lagos", 3)
5. Call get_weather_alert("Lagos")
6. Call get_all() to read everything
```

---

## Error Handling

If Open-Meteo is unavailable, every method returns a clean error message instead of failing silently:

```json
{
  "error": "Open-Meteo API is down. Please try again later.",
  "status": "unavailable"
}
```

If you request an unsupported city:

```json
{
  "error": "Cairo is not a supported city.",
  "status": "unsupported"
}
```

Validators reach consensus on error states too — so the contract never gets stuck during downtime.

---

## License

MIT