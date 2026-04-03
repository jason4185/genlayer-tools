# { "Depends": "py-genlayer:test" }

from genlayer import *
import json
import typing

ASSET_INFO = {
    "BTCUSDT":   {"name": "Bitcoin",                       "abbr": "BTC",     "category": "crypto",    "exchange": "Binance"},
    "ETHUSDT":   {"name": "Ethereum",                      "abbr": "ETH",     "category": "crypto",    "exchange": "Binance"},
    "SOLUSDT":   {"name": "Solana",                        "abbr": "SOL",     "category": "crypto",    "exchange": "Binance"},
    "BNBUSDT":   {"name": "BNB",                           "abbr": "BNB",     "category": "crypto",    "exchange": "Binance"},
    "XRPUSDT":   {"name": "XRP",                           "abbr": "XRP",     "category": "crypto",    "exchange": "Binance"},
    "ADAUSDT":   {"name": "Cardano",                       "abbr": "ADA",     "category": "crypto",    "exchange": "Binance"},
    "DOGEUSDT":  {"name": "Dogecoin",                      "abbr": "DOGE",    "category": "crypto",    "exchange": "Binance"},
    "LINKUSDT":  {"name": "Chainlink",                     "abbr": "LINK",    "category": "crypto",    "exchange": "Binance"},
    "MATICUSDT": {"name": "Polygon",                       "abbr": "MATIC",   "category": "crypto",    "exchange": "Binance"},
    "AVAXUSDT":  {"name": "Avalanche",                     "abbr": "AVAX",    "category": "crypto",    "exchange": "Binance"},
    "USD/EUR":   {"name": "US Dollar / Euro",              "abbr": "USD/EUR", "category": "forex",     "exchange": "Frankfurter"},
    "USD/GBP":   {"name": "US Dollar / British Pound",     "abbr": "USD/GBP", "category": "forex",     "exchange": "Frankfurter"},
    "USD/NGN":   {"name": "US Dollar / Nigerian Naira",    "abbr": "USD/NGN", "category": "forex",     "exchange": "Frankfurter"},
    "USD/JPY":   {"name": "US Dollar / Japanese Yen",      "abbr": "USD/JPY", "category": "forex",     "exchange": "Frankfurter"},
    "USD/CAD":   {"name": "US Dollar / Canadian Dollar",   "abbr": "USD/CAD", "category": "forex",     "exchange": "Frankfurter"},
    "USD/AUD":   {"name": "US Dollar / Australian Dollar", "abbr": "USD/AUD", "category": "forex",     "exchange": "Frankfurter"},
    "EUR/GBP":   {"name": "Euro / British Pound",          "abbr": "EUR/GBP", "category": "forex",     "exchange": "Frankfurter"},
    "XAU/USD":   {"name": "Gold",                          "abbr": "XAU",     "category": "commodity", "exchange": "Frankfurter"},
    "XAG/USD":   {"name": "Silver",                        "abbr": "XAG",     "category": "commodity", "exchange": "Frankfurter"},
    "XPT/USD":   {"name": "Platinum",                      "abbr": "XPT",     "category": "commodity", "exchange": "Frankfurter"},
    "XPD/USD":   {"name": "Palladium",                     "abbr": "XPD",     "category": "commodity", "exchange": "Frankfurter"},
}


class PriceOracle(gl.Contract):

    cache:     str
    heartbeat: str

    def __init__(self):
        self.cache     = "{}"
        self.heartbeat = "{}"

    # ── CRYPTO ─────────────────────────────────────────────────────

    @gl.public.write
    def get_crypto(self, symbol: str) -> typing.Any:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"

        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url, mode="text")
                if not raw or raw.strip() == "null":
                    return json.dumps({"error": "Binance API is down. Please try again later.", "status": "unavailable"})
                data   = json.loads(raw)
                price  = float(data["lastPrice"])
                change = float(data["priceChangePercent"])
                volume = float(data["volume"])
                vusdt  = float(data["quoteVolume"])
                info   = ASSET_INFO.get(symbol, {})
                chgdir = "up" if change >= 0 else "down"
                result = {
                    "symbol":        symbol,
                    "name":          info.get("name", symbol),
                    "abbr":          info.get("abbr", symbol),
                    "category":      info.get("category", "crypto"),
                    "exchange":      info.get("exchange", "Binance"),
                    "price":         price,
                    "display_price": "$" + str(round(price, 2)),
                    "change_pct":    round(change, 2),
                    "change_dir":    chgdir,
                    "high":          float(data["highPrice"]),
                    "low":           float(data["lowPrice"]),
                    "open":          float(data["openPrice"]),
                    "volume":        volume,
                    "volume_usdt":   vusdt,
                    "status":        "ok",
                }
                return json.dumps(result, sort_keys=True)
            except Exception:
                return json.dumps({"error": "Binance API is down. Please try again later.", "status": "unavailable"})

        fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same crypto price. They are equivalent if both show an API error, or if price values are within 2% and symbol matches.")
        all_prices         = json.loads(self.cache)
        all_prices[symbol] = json.loads(fresh)
        self.cache         = json.dumps(all_prices, sort_keys=True)
        hb                 = json.loads(self.heartbeat)
        hb[symbol]         = "updated"
        self.heartbeat     = json.dumps(hb, sort_keys=True)

    @gl.public.write
    def get_multiple_crypto(self, symbols: list) -> typing.Any:
        all_prices = json.loads(self.cache)
        hb         = json.loads(self.heartbeat)
        for symbol in symbols:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            def fetch() -> str:
                try:
                    raw = gl.nondet.web.render(url, mode="text")
                    if not raw or raw.strip() == "null":
                        return json.dumps({"error": "Binance API is down. Please try again later.", "status": "unavailable"})
                    data   = json.loads(raw)
                    price  = float(data["lastPrice"])
                    change = float(data["priceChangePercent"])
                    volume = float(data["volume"])
                    vusdt  = float(data["quoteVolume"])
                    info   = ASSET_INFO.get(symbol, {})
                    chgdir = "up" if change >= 0 else "down"
                    result = {
                        "symbol":        symbol,
                        "name":          info.get("name", symbol),
                        "abbr":          info.get("abbr", symbol),
                        "category":      info.get("category", "crypto"),
                        "exchange":      info.get("exchange", "Binance"),
                        "price":         price,
                        "display_price": "$" + str(round(price, 2)),
                        "change_pct":    round(change, 2),
                        "change_dir":    chgdir,
                        "high":          float(data["highPrice"]),
                        "low":           float(data["lowPrice"]),
                        "open":          float(data["openPrice"]),
                        "volume":        volume,
                        "volume_usdt":   vusdt,
                        "status":        "ok",
                    }
                    return json.dumps(result, sort_keys=True)
                except Exception:
                    return json.dumps({"error": "Binance API is down. Please try again later.", "status": "unavailable"})
            fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same crypto price. They are equivalent if both show an API error, or if price values are within 2%.")
            all_prices[symbol] = json.loads(fresh)
            hb[symbol]         = "updated"
        self.cache     = json.dumps(all_prices, sort_keys=True)
        self.heartbeat = json.dumps(hb, sort_keys=True)

    # ── FOREX ──────────────────────────────────────────────────────

    @gl.public.write
    def get_forex(self, base: str, target: str) -> typing.Any:
        symbol = base + "/" + target
        url    = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url, mode="text")
                if not raw or raw.strip() == "null":
                    return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
                data   = json.loads(raw)
                rate   = data["rates"][target]
                info   = ASSET_INFO.get(symbol, {})
                result = {
                    "symbol":        symbol,
                    "name":          info.get("name", symbol),
                    "abbr":          info.get("abbr", symbol),
                    "category":      "forex",
                    "exchange":      "Frankfurter",
                    "base":          base,
                    "target":        target,
                    "price":         rate,
                    "display_price": str(round(rate, 4)) + " " + target,
                    "date":          data.get("date", ""),
                    "status":        "ok",
                }
                return json.dumps(result, sort_keys=True)
            except Exception:
                return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
        fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same forex rate. They are equivalent if both show an API error, or if rate values are within 0.5% and currencies match.")
        all_prices         = json.loads(self.cache)
        all_prices[symbol] = json.loads(fresh)
        self.cache         = json.dumps(all_prices, sort_keys=True)
        hb                 = json.loads(self.heartbeat)
        hb[symbol]         = "updated"
        self.heartbeat     = json.dumps(hb, sort_keys=True)

    @gl.public.write
    def get_multiple_forex(self, pairs: list) -> typing.Any:
        all_prices = json.loads(self.cache)
        hb         = json.loads(self.heartbeat)
        for pair in pairs:
            base   = pair[0]
            target = pair[1]
            symbol = base + "/" + target
            url    = f"https://api.frankfurter.app/latest?from={base}&to={target}"
            def fetch() -> str:
                try:
                    raw = gl.nondet.web.render(url, mode="text")
                    if not raw or raw.strip() == "null":
                        return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
                    data   = json.loads(raw)
                    rate   = data["rates"][target]
                    info   = ASSET_INFO.get(symbol, {})
                    result = {
                        "symbol":        symbol,
                        "name":          info.get("name", symbol),
                        "abbr":          info.get("abbr", symbol),
                        "category":      "forex",
                        "exchange":      "Frankfurter",
                        "base":          base,
                        "target":        target,
                        "price":         rate,
                        "display_price": str(round(rate, 4)) + " " + target,
                        "date":          data.get("date", ""),
                        "status":        "ok",
                    }
                    return json.dumps(result, sort_keys=True)
                except Exception:
                    return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
            fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same forex rate. They are equivalent if both show an API error, or if rate values are within 0.5%.")
            all_prices[symbol] = json.loads(fresh)
            hb[symbol]         = "updated"
        self.cache     = json.dumps(all_prices, sort_keys=True)
        self.heartbeat = json.dumps(hb, sort_keys=True)

    # ── COMMODITIES ────────────────────────────────────────────────

    @gl.public.write
    def get_commodity(self, symbol: str) -> typing.Any:
        parts  = symbol.split("/")
        base   = parts[0]
        target = parts[1]
        url    = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        def fetch() -> str:
            try:
                raw = gl.nondet.web.render(url, mode="text")
                if not raw or raw.strip() == "null":
                    return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
                data   = json.loads(raw)
                rate   = data["rates"][target]
                info   = ASSET_INFO.get(symbol, {})
                result = {
                    "symbol":        symbol,
                    "name":          info.get("name", symbol),
                    "abbr":          info.get("abbr", base),
                    "category":      "commodity",
                    "exchange":      "Frankfurter",
                    "base":          base,
                    "target":        target,
                    "price":         rate,
                    "display_price": "$" + str(round(rate, 2)),
                    "date":          data.get("date", ""),
                    "status":        "ok",
                }
                return json.dumps(result, sort_keys=True)
            except Exception:
                return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
        fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same commodity price. They are equivalent if both show an API error, or if price values are within 1% and symbol matches.")
        all_prices         = json.loads(self.cache)
        all_prices[symbol] = json.loads(fresh)
        self.cache         = json.dumps(all_prices, sort_keys=True)
        hb                 = json.loads(self.heartbeat)
        hb[symbol]         = "updated"
        self.heartbeat     = json.dumps(hb, sort_keys=True)

    @gl.public.write
    def get_multiple_commodities(self, symbols: list) -> typing.Any:
        all_prices = json.loads(self.cache)
        hb         = json.loads(self.heartbeat)
        for symbol in symbols:
            parts  = symbol.split("/")
            base   = parts[0]
            target = parts[1]
            url    = f"https://api.frankfurter.app/latest?from={base}&to={target}"
            def fetch() -> str:
                try:
                    raw = gl.nondet.web.render(url, mode="text")
                    if not raw or raw.strip() == "null":
                        return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
                    data   = json.loads(raw)
                    rate   = data["rates"][target]
                    info   = ASSET_INFO.get(symbol, {})
                    result = {
                        "symbol":        symbol,
                        "name":          info.get("name", symbol),
                        "abbr":          info.get("abbr", base),
                        "category":      "commodity",
                        "exchange":      "Frankfurter",
                        "base":          base,
                        "target":        target,
                        "price":         rate,
                        "display_price": "$" + str(round(rate, 2)),
                        "date":          data.get("date", ""),
                        "status":        "ok",
                    }
                    return json.dumps(result, sort_keys=True)
                except Exception:
                    return json.dumps({"error": "Frankfurter API is down. Please try again later.", "status": "unavailable"})
            fresh              = gl.eq_principle.prompt_comparative(fetch, "The outputs represent the same commodity price. They are equivalent if both show an API error, or if price values are within 1%.")
            all_prices[symbol] = json.loads(fresh)
            hb[symbol]         = "updated"
        self.cache     = json.dumps(all_prices, sort_keys=True)
        self.heartbeat = json.dumps(hb, sort_keys=True)

    # ── AI SUMMARIES ───────────────────────────────────────────────

    @gl.public.write
    def get_market_summary(self) -> typing.Any:
        all_prices = json.loads(self.cache)
        if not all_prices:
            return
        def summarize() -> str:
            prompt = (
                f"You are a professional financial analyst. Based on this market data, "
                f"write a concise two-sentence briefing covering crypto, forex and commodity trends:\n\n"
                f"{json.dumps(all_prices)}\n\n"
                f"Respond with only the briefing, nothing else."
            )
            return gl.nondet.exec_prompt(prompt)
        summary                      = gl.eq_principle.prompt_comparative(summarize, "Both outputs summarize the same market. They are equivalent if they describe the same trend direction.")
        all_prices["market_summary"] = summary
        self.cache                   = json.dumps(all_prices, sort_keys=True)

    @gl.public.write
    def get_summary_by_category(self, category: str) -> typing.Any:
        all_prices = json.loads(self.cache)
        filtered   = {}
        for sym, data in all_prices.items():
            if isinstance(data, dict) and data.get("category") == category and data.get("status") == "ok":
                filtered[sym] = data
        if not filtered:
            return
        def summarize() -> str:
            prompt = (
                f"You are a professional financial analyst. Based on this {category} market data, "
                f"write one sentence summarizing current {category} trends:\n\n"
                f"{json.dumps(filtered)}\n\n"
                f"Respond with only the summary sentence, nothing else."
            )
            return gl.nondet.exec_prompt(prompt)
        summary = gl.eq_principle.prompt_comparative(summarize, "Both outputs summarize the same market data. They are equivalent if they describe the same trend direction.")
        all_prices[category + "_summary"] = summary
        self.cache                        = json.dumps(all_prices, sort_keys=True)

    @gl.public.write
    def get_portfolio_value(self, holdings: str) -> typing.Any:
        all_prices  = json.loads(self.cache)
        portfolio   = json.loads(holdings)
        total_value = 0.0
        breakdown   = []
        for symbol, amount in portfolio.items():
            if symbol not in all_prices:
                breakdown.append({"symbol": symbol, "error": "Price not cached."})
                continue
            price_data = all_prices[symbol]
            if price_data.get("status") != "ok":
                breakdown.append({"symbol": symbol, "error": "Price unavailable."})
                continue
            price       = price_data["price"]
            value       = price * amount
            total_value = total_value + value
            breakdown.append({
                "symbol":        symbol,
                "name":          price_data.get("name", symbol),
                "abbr":          price_data.get("abbr", symbol),
                "amount":        amount,
                "price":         price,
                "display_price": price_data.get("display_price", ""),
                "value_usd":     round(value, 2),
                "display_value": "$" + str(round(value, 2)),
            })
        result              = {
            "total_usd":     round(total_value, 2),
            "display_total": "$" + str(round(total_value, 2)),
            "breakdown":     breakdown,
        }
        all_prices["portfolio"] = result
        self.cache              = json.dumps(all_prices, sort_keys=True)

    # ── FREE READ METHODS ──────────────────────────────────────────

    @gl.public.view
    def get_cached(self, symbol: str) -> str:
        all_prices = json.loads(self.cache)
        if symbol in all_prices:
            return json.dumps(all_prices[symbol])
        return json.dumps({"error": symbol + " not cached. Call get_crypto, get_forex or get_commodity first."})

    @gl.public.view
    def get_all(self) -> str:
        return self.cache

    @gl.public.view
    def get_all_crypto(self) -> str:
        all_prices = json.loads(self.cache)
        result     = {}
        for sym, data in all_prices.items():
            if isinstance(data, dict) and data.get("category") == "crypto":
                result[sym] = data
        return json.dumps(result)

    @gl.public.view
    def get_all_forex(self) -> str:
        all_prices = json.loads(self.cache)
        result     = {}
        for sym, data in all_prices.items():
            if isinstance(data, dict) and data.get("category") == "forex":
                result[sym] = data
        return json.dumps(result)

    @gl.public.view
    def get_all_commodities(self) -> str:
        all_prices = json.loads(self.cache)
        result     = {}
        for sym, data in all_prices.items():
            if isinstance(data, dict) and data.get("category") == "commodity":
                result[sym] = data
        return json.dumps(result)

    @gl.public.view
    def get_asset_info(self, symbol: str) -> str:
        info = ASSET_INFO.get(symbol)
        if not info:
            return json.dumps({"error": symbol + " not found in asset registry."})
        return json.dumps({
            "symbol":   symbol,
            "name":     info["name"],
            "abbr":     info["abbr"],
            "category": info["category"],
            "exchange": info["exchange"],
        })

    @gl.public.view
    def get_biggest_mover(self) -> str:
        all_prices  = json.loads(self.cache)
        best_symbol = ""
        best_change = 0.0
        for sym, data in all_prices.items():
            if not isinstance(data, dict):
                continue
            if data.get("status") != "ok":
                continue
            if "change_pct" not in data:
                continue
            chg = data["change_pct"]
            if chg < 0:
                chg = chg * -1
            if chg > best_change:
                best_change = chg
                best_symbol = sym
        if best_symbol == "":
            return json.dumps({"error": "No crypto data cached yet."})
        winner = all_prices[best_symbol]
        return json.dumps({
            "symbol":        best_symbol,
            "change_pct":    winner["change_pct"],
            "change_dir":    winner["change_dir"],
            "display_price": winner.get("display_price", ""),
            "name":          winner.get("name", ""),
            "abbr":          winner.get("abbr", ""),
        })

    @gl.public.view
    def get_movers_by_direction(self, direction: str) -> str:
        all_prices = json.loads(self.cache)
        result     = {}
        for sym, data in all_prices.items():
            if not isinstance(data, dict):
                continue
            if data.get("status") != "ok":
                continue
            if data.get("change_dir") == direction:
                result[sym] = {
                    "symbol":        sym,
                    "name":          data.get("name", sym),
                    "abbr":          data.get("abbr", sym),
                    "display_price": data.get("display_price", ""),
                    "change_pct":    data.get("change_pct", 0),
                    "change_dir":    data.get("change_dir", ""),
                }
        if not result:
            return json.dumps({"message": "No assets found moving " + direction + "."})
        return json.dumps(result)

    @gl.public.view
    def check_liquidity(self, symbol: str) -> str:
        all_prices = json.loads(self.cache)
        if symbol not in all_prices:
            return json.dumps({"error": symbol + " not cached. Call get_crypto first."})
        data = all_prices[symbol]
        if data.get("status") != "ok":
            return json.dumps({"error": "Price data unavailable for liquidity check."})
        if "volume_usdt" not in data:
            return json.dumps({"error": symbol + " is not a crypto pair. Liquidity check is for crypto only."})
        volume = data["volume_usdt"]
        if volume >= 100000000:
            level   = "very_high"
            message = "Excellent liquidity. Suitable for large trades."
        elif volume >= 10000000:
            level   = "high"
            message = "Good liquidity. Suitable for most trades."
        elif volume >= 1000000:
            level   = "medium"
            message = "Moderate liquidity. Use limit orders for large trades."
        else:
            level   = "low"
            message = "Low liquidity. Exercise caution with large trades."
        return json.dumps({
            "symbol":         symbol,
            "volume_usdt":    volume,
            "display_volume": "$" + str(round(volume, 0)),
            "liquidity":      level,
            "message":        message,
        })

    @gl.public.view
    def is_price_stale(self, symbol: str) -> str:
        hb = json.loads(self.heartbeat)
        if symbol not in hb:
            return json.dumps({"symbol": symbol, "stale": True, "reason": symbol + " has never been fetched."})
        return json.dumps({"symbol": symbol, "stale": False, "reason": symbol + " is in cache.", "heartbeat": hb[symbol]})

    @gl.public.view
    def get_staleness_report(self) -> str:
        hb         = json.loads(self.heartbeat)
        all_prices = json.loads(self.cache)
        cached     = []
        missing    = []
        for sym, info in ASSET_INFO.items():
            if sym in hb:
                data = all_prices.get(sym, {})
                cached.append({
                    "symbol":   sym,
                    "name":     info["name"],
                    "abbr":     info["abbr"],
                    "category": info["category"],
                    "status":   data.get("status", "unknown"),
                })
            else:
                missing.append({
                    "symbol":   sym,
                    "name":     info["name"],
                    "abbr":     info["abbr"],
                    "category": info["category"],
                })
        return json.dumps({
            "total_supported": len(ASSET_INFO),
            "total_cached":    len(cached),
            "total_missing":   len(missing),
            "cached":          cached,
            "not_cached":      missing,
        })

    @gl.public.view
    def list_supported_assets(self) -> str:
        assets = []
        for sym, info in ASSET_INFO.items():
            assets.append({
                "symbol":   sym,
                "name":     info["name"],
                "abbr":     info["abbr"],
                "category": info["category"],
                "exchange": info["exchange"],
            })
        return json.dumps(assets)