# GenLayer General Price Feed

The first multi-asset price oracle on GenLayer. Crypto, forex and commodities — all verified on-chain, no API keys, no oracles, no middlemen.

---

## What Makes This Different

Every price you read from this contract was independently fetched by five AI validators and agreed upon before being written on-chain. You are not trusting a single data source. You are reading a result that five separate nodes verified.

It covers three asset classes in one contract:

- **Crypto** — live prices from the Binance public API
- **Forex** — live exchange rates from the Frankfurter API
- **Commodities** — Gold, Silver, Platinum and Palladium from Frankfurter

No sign-ups. No API keys. Deploy and go.

---

## APIs Used

| API | Data | Endpoint |
|---|---|---|
| Binance | Crypto prices | `api.binance.com/api/v3/ticker/24hr` |
| Frankfurter | Forex rates + Commodities | `api.frankfurter.app/latest` |

Both are free and publicly accessible with no authentication required.

---

## Supported Assets

**Crypto (10 pairs)**
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, LINK, MATIC, AVAX — all priced in USDT

**Forex (7 pairs)**
USD/EUR, USD/GBP, USD/NGN, USD/JPY, USD/CAD, USD/AUD, EUR/GBP

**Commodities (4)**
Gold (XAU), Silver (XAG), Platinum (XPT), Palladium (XPD) — all priced in USD

---

## Every Price Response Includes

| Field | Description | Example |
|---|---|---|
| `symbol` | Asset identifier | `BTCUSDT` |
| `name` | Full asset name | `Bitcoin` |
| `abbr` | Short abbreviation | `BTC` |
| `category` | Asset class | `crypto` |
| `exchange` | Data source | `Binance` |
| `price` | Raw price number | `84231.5` |
| `display_price` | Formatted for display | `$84231.5` |
| `change_pct` | 24h % change | `-1.42` |
| `change_dir` | Price direction | `down` |
| `status` | Data validity | `ok` |

Crypto responses also include `high`, `low`, `open`, `volume` and `volume_usdt` for liquidity checks.

---

## Methods

### Fetch (requires a transaction)

| Method | What it does |
|---|---|
| `get_crypto(symbol)` | Fetch one crypto pair |
| `get_multiple_crypto(symbols)` | Fetch multiple crypto pairs — one transaction |
| `get_forex(base, target)` | Fetch one forex rate |
| `get_multiple_forex(pairs)` | Fetch multiple forex rates — one transaction |
| `get_commodity(symbol)` | Fetch one commodity price |
| `get_multiple_commodities(symbols)` | Fetch multiple commodities — one transaction |
| `get_market_summary()` | AI two-sentence market briefing |
| `get_summary_by_category(category)` | AI summary for crypto, forex or commodity |
| `get_portfolio_value(holdings)` | Calculate total USD value of your holdings |

### Read (free — no transaction)

| Method | What it does |
|---|---|
| `get_all()` | Every cached asset at once |
| `get_all_crypto()` | Only cached crypto prices |
| `get_all_forex()` | Only cached forex rates |
| `get_all_commodities()` | Only cached commodity prices |
| `get_cached(symbol)` | One specific asset from cache |
| `get_asset_info(symbol)` | Full metadata — name, abbr, category, exchange |
| `get_biggest_mover()` | Asset with highest absolute % change |
| `get_movers_by_direction(direction)` | All assets moving "up" or "down" |
| `check_liquidity(symbol)` | Liquidity rating for any crypto pair |
| `is_price_stale(symbol)` | Check if a symbol has been fetched |
| `get_staleness_report()` | Full report of cached vs missing assets |
| `list_supported_assets()` | All 21 supported assets |

---

## Quick Start

```
1. Paste contract.py into GenLayer Studio
2. Deploy — no constructor arguments needed
3. Call get_multiple_crypto(["BTCUSDT","ETHUSDT","SOLUSDT"])
4. Call get_multiple_forex([["USD","EUR"],["USD","GBP"]])
5. Call get_multiple_commodities(["XAU/USD","XAG/USD"])
6. Call get_all() to read everything at once
```

---

## Standout Features

### Liquidity Check
```
check_liquidity("BTCUSDT")
```
Returns one of four levels — `very_high`, `high`, `medium`, or `low` — based on 24h USDT trading volume. Tells you instantly if an asset is safe to trade in size.

### Portfolio Calculator
```
get_portfolio_value('{"BTCUSDT": 0.5, "ETHUSDT": 2.0}')
```
Pass your holdings as a JSON string. Get back total USD value and a per-asset breakdown with display prices.

### Staleness Report
```
get_staleness_report()
```
Shows exactly which of the 21 supported assets are cached and which still need fetching. Useful for monitoring and keeping your data fresh.

### AI Market Summary
```
get_market_summary()
get_summary_by_category("crypto")
```
GenLayer's native LLM reads your cached prices and writes a professional market briefing on-chain. No other blockchain can do this.

---

## Error Handling

If an API goes down, every method returns a clean error instead of failing silently:

```json
{
  "error": "Binance API is down. Please try again later.",
  "status": "unavailable"
}
```

Validators reach consensus on the error state too — so the contract never gets stuck.

---

## How Consensus Works

Each write transaction runs across five GenLayer validators simultaneously. Each validator fetches the price independently. Since prices shift by the millisecond, `eq_principle.prompt_comparative` is used — validators agree if prices are within 2% of each other for crypto and 0.5% for forex. The result is only written on-chain when all validators agree.

---

## License

MIT