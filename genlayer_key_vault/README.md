# GenLayer Key Vault

Every week, developers accidentally expose private API keys in public repositories, transaction logs, or contract state. Once exposed, a key can be used to drain accounts, exceed rate limits, or access sensitive data — and you may not know until the damage is done.

On a blockchain, the problem is worse. Everything stored in plain contract state is publicly readable by anyone. Most developers building Intelligent Contracts on GenLayer have no safe way to use a private API key without it being visible to the world.

This contract fixes that.

---

## Why Only GenLayer Can Do This

Traditional smart contracts on Ethereum or Solana cannot access the internet at all — so the problem of private API keys never even comes up. They use oracles, which introduce centralization.

GenLayer Intelligent Contracts can access any URL directly. That power creates a new challenge: how do you use a private API key without exposing it?

The answer is GenLayer's **non-deterministic execution block**. Code inside a `nondet` block runs on each validator privately during consensus. The key is loaded, used to build the URL, and the fetch happens — but only the response is written to the chain. The key never appears in the transaction output, the state read methods, or the audit log.

No other blockchain can offer this pattern. It is unique to GenLayer.

---

## How It Works

### Step 1 — Deploy with your API key and wallet address

In GenLayer Studio, paste the contract and click **Deploy new instance**. Fill in two constructor fields:

- `api_key` — your private API key from any provider
- `owner_address` — your wallet address e.g. `0xe2...7Eb9`

Your key is stored privately. Your wallet becomes the contract owner.

### Step 2 — Whitelist addresses

```
add_allowed_caller("0xAddress", "0xYourOwnerAddress")
```

Or add multiple at once:

```
bulk_add_callers(["0xAddr1","0xAddr2"], "0xYourOwnerAddress")
```

### Step 3 — Make a secure API call

**Key appended to URL:**
```
fetch_with_key("https://api.example.com/data?token=")
```

**Key as named query parameter:**
```
fetch_with_key_param("https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT&", "apiKey")
```

### Step 4 — Verify the key was never exposed

```
get_security_status()
```

Returns:
```json
{
  "api_key_stored": "yes",
  "api_key_exposed": "no",
  "calls_made": "1",
  "calls_remaining": "99"
}
```

The key exists. It is used. It is never shown.

---

## Proof of Concept — MEXC Exchange API

The contract was tested with a real private API key from **MEXC Exchange**.

**Setup:**
- Private MEXC Access Key stored as `api_key` at deploy time
- `fetch_with_key_param` called with MEXC ticker endpoint
- `apiKey` used as the query parameter name

**Result:**
```json
{
  "status": "ok",
  "response": {
    "symbol": "BTCUSDT",
    "price": "6700.13"
  }
}
```

**Security confirmation:**
```json
{
  "api_key_stored": "yes",
  "api_key_exposed": "no"
}
```

Real private key. Real data. Key never exposed.

---

## Owner Controls

All owner methods require you to pass your `owner_address` to verify identity:

| Method | What it does |
|---|---|
| `add_allowed_caller(address, owner)` | Whitelist one address |
| `bulk_add_callers(addresses, owner)` | Whitelist multiple at once |
| `remove_allowed_caller(address, owner)` | Remove from whitelist |
| `rotate_key(new_key, owner)` | Replace API key without redeploying |
| `set_rate_limit(limit, owner)` | Set max number of API calls |
| `reset_call_count(owner)` | Reset call counter |
| `pause(owner)` | Emergency stop |
| `unpause(owner)` | Re-enable contract |
| `transfer_ownership(new_owner, owner)` | Hand over full control |

---

## Free Read Methods

| Method | What it returns |
|---|---|
| `get_security_status()` | Full report — key stored, not exposed, callers, calls remaining |
| `get_whitelist()` | All whitelisted addresses |
| `get_caller_count()` | Number of whitelisted addresses |
| `is_caller_allowed(address)` | True or false for one address |
| `get_call_count()` | Calls made vs rate limit |
| `get_remaining_calls()` | Remaining calls with readable message |
| `is_paused_status()` | Whether contract is active or paused |
| `get_key_version()` | Current version and rotation count |
| `get_owner()` | Current owner wallet address |
| `get_last_response()` | Last API response — never the key |
| `get_audit_log()` | Full history of every action |

---

## Security Features

**Address Validation** — every address input validated before any action. Must start with `0x`, be exactly 42 characters, hex only.

**Audit Log** — every action recorded — calls, rejections, rotations, bulk operations, ownership transfers. Stores last 50 entries.

**Rate Limiting** — default 100 calls. Owner adjusts or resets anytime. Clear error stored in `last_response` when limit is hit.

**Emergency Pause** — owner blocks all fetch calls instantly with `pause()`.

**Key Rotation** — replace key without redeploying. Version number increments automatically.

**Ownership Transfer** — full control handed to another wallet. Logged in audit trail. Irreversible unless new owner transfers back.

---

## Testnet Limitations

Two limitations were discovered during testing on Testnet Bradbury and documented here for full transparency.

### 1. `gl.message.sender_account` Not Supported

`gl.message.sender_account` identifies the wallet making a call. Without it, the whitelist cannot be automatically enforced during fetch calls on testnet — any wallet can currently trigger `fetch_with_key`.

**Workaround:** All owner-only methods require the caller to pass their `owner_address` explicitly. The contract verifies it against the stored owner. Full automatic enforcement is implemented in the code and works on mainnet.

### 2. `assert` Statements Do Not Always Revert Transactions

On Testnet Bradbury, failed assertions sometimes do not stop transaction execution. Transactions finalize as ACCEPTED even when a check fails.

**Workaround:** Rejections are logged to the audit log with a clear reason. Fetch errors are stored in `last_response` so the caller can read exactly what went wrong.

### Testnet vs Mainnet

| Feature | Testnet | Mainnet |
|---|---|---|
| API key privacy | ✅ | ✅ |
| Rate limiting | ✅ | ✅ |
| Pause / unpause | ✅ | ✅ |
| Key rotation | ✅ | ✅ |
| Ownership transfer | ✅ | ✅ |
| Address validation | ✅ | ✅ |
| Audit log | ✅ | ✅ |
| Whitelist management | ✅ | ✅ |
| Whitelist enforcement during fetch | ⚠️ Testnet limitation | ✅ |
| `assert` transaction revert | ⚠️ Partial | ✅ |

---

## Compatible APIs

Works with any API that accepts server-side requests and uses key-in-URL or query parameter authentication.

**Confirmed working on GenLayer testnet:**
- MEXC Exchange API ✅
- Binance Public API ✅
- Frankfurter API ✅

**Blocked by GenLayer validator network on testnet:**
- OpenWeatherMap — requires browser User-Agent header
- NASA API — same restriction

**Pattern does not support:**
- APIs requiring key in HTTP headers (Bearer/Authorization)
- APIs requiring POST requests with key in request body

---

## Quick Start

```
1. Paste contract.py into GenLayer Studio
2. Deploy with your api_key and owner_address
3. Call add_allowed_caller to whitelist your address
4. Call fetch_with_key_param with your API URL and param name
5. Call get_last_response to read the result
6. Call get_security_status to confirm key was never exposed
```

---

## License

MIT