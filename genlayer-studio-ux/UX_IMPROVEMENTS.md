# GenLayer Studio — UX Improvements & Known Limitations

This document was written after building and testing four Intelligent Contracts on GenLayer Studio — a price feed oracle, a weather oracle, a social media oracle and a secure API key gateway. The issues listed here were all encountered during real development sessions, not theoretical scenarios. Each one includes what happened, how it affected the workflow, a suggested fix, and where applicable a screenshot from testing.

---

## UX Issues Found During Development

### 1. Schema Loading Error Gives No Detail

**What happened:**
When a contract fails to load its schema, Studio shows a single message with no further context:

> "Could not load contract schema."

During testing this error appeared multiple times for different reasons — an `int` state variable, an f-string with format specs, a missing `__init__` constructor, and unsupported Python features like `**dict` unpacking. None of these causes were hinted at by the error message.


**Impact:**
Each occurrence required trial and error to identify the cause. Across all four contracts this cost several hours of debugging time that a better error message would have eliminated entirely.

**Suggested fix:**
Display the specific reason and line number that caused the schema to fail. Example:

> "Could not load contract schema. Line 34: `int` state variables are not supported in GenVM. Use fixed-size types like `i32`, `u256`, or `bigint` instead."

---

### 2. Array Input Has No Format Example

**What happened:**
Write methods that accept a `list` parameter show a plain input field labelled `array`. No example, no placeholder, no tooltip.


**Impact:**
It was not immediately clear whether to type `["BTCUSDT","ETHUSDT"]`, `BTCUSDT, ETHUSDT`, or something else. This caused confusion when testing `get_multiple_crypto` and `bulk_add_callers`.

**Suggested fix:**
Show a placeholder inside the input field with the correct format:

> `["BTCUSDT", "ETHUSDT", "SOLUSDT"]`

Alternatively, provide a dynamic input where items can be added one by one with an **Add item** button.

---

### 3. JSON Responses Display as Raw Escaped Text

**What happened:**
All contract responses are displayed as raw escaped JSON strings. Even short responses are difficult to read.


**Impact:**
For contracts returning multiple nested fields like the price feed or weather oracle, reading the raw output required significant mental effort. Developers should not have to parse escape characters to understand their contract's state.

**Suggested fix:**
Render JSON responses in a formatted, collapsible tree structure — similar to how browser DevTools or Postman display API responses.

---

### 4. UNDETERMINED Status Has No Explanation

**What happened:**
When validators fail to reach consensus, transactions show `UNDETERMINED` status with no accompanying explanation.


**Impact:**
During early testing of `get_posts` and `get_multiple_crypto`, multiple transactions returned UNDETERMINED. Without any explanation it was unclear whether the issue was a code bug, a network problem, or a consensus configuration issue. The actual cause was that `strict_eq` was being used for live data that changes between validator fetches — but this took significant time to diagnose.

**Suggested fix:**
Show a brief contextual message when UNDETERMINED occurs:

> "Validators could not agree on the same result. If you are fetching live data that changes frequently, consider switching from `eq_principle.strict_eq` to `eq_principle.prompt_comparative` with a tolerance range."

---

### 5. Simulation Mode Is Easy to Miss

**What happened:**
The Simulation Mode checkbox is placed directly next to the Write Methods panel with no clear label explaining what it does. When checked, transactions execute but do not save state to the blockchain.


**Impact:**
During testing, Simulation Mode was accidentally left checked. The contract appeared to execute successfully — transactions showed FINALIZED — but `get_all()` kept returning `"{}"` because nothing was actually written to the chain. This caused several hours of confusion and multiple redeployments before the cause was identified.

**Suggested fix:**
Display a clearly visible warning banner whenever Simulation Mode is active:

> ⚠️ Simulation Mode is ON. Transactions will not save state to the blockchain.

Additionally, consider auto-unchecking Simulation Mode after each simulated run to prevent accidental repeat.

---

### 6. Upgrade Code Shows No Confirmation of What Changed

**What happened:**
After clicking Upgrade code, Studio redeploys the contract silently. There is no feedback showing whether the new code was applied or what changed between versions.

**Impact:**
During testing it was sometimes unclear whether the upgraded contract contained the latest edits or a previously cached version. This led to situations where the same bug appeared to persist after being fixed.

**Suggested fix:**
After a successful upgrade, show a brief summary:

> "Upgraded successfully. Methods added: `get_all_crypto`, `get_all_forex`. Methods modified: `get_cached`. Methods removed: none."

---

### 7. Read Methods Do Not Refresh After a Write

**What happened:**
After a write transaction finalizes, read method responses remain unchanged. The developer must manually click Call Contract again to see the updated state.

**Impact:**
This is easy to forget, especially when testing multiple methods in sequence. New developers may incorrectly conclude that their write transaction did not work simply because they forgot to manually refresh the read method.

**Suggested fix:**
Automatically refresh all read method responses after a write transaction reaches FINALIZED status.

---



## Known Limitations Encountered on GenLayer Studio

### 1. Many Common APIs Block GenLayer Validators

During testing across all four contracts, several widely used APIs returned errors not because of incorrect code but because they identified GenLayer validator requests as automated bots and blocked them entirely.

**APIs confirmed as blocked on testnet:**

| API | Reason |
|---|---|
| OpenWeatherMap | Requires browser User-Agent header |
| NASA API | Same restriction |
| Reddit API | Returns 403 — explicitly blocks non-browser requests |

**APIs confirmed as accessible from GenLayer validators:**

| API | Used in |
|---|---|
| Binance public API | Price Feed |
| Frankfurter API | Price Feed, Key Vault |
| Open-Meteo API | Weather Oracle |
| Hacker News Firebase API | Social Media Oracle |
| MEXC Exchange API | Key Vault |

This is not a GenLayer code issue — it is a restriction imposed by the API providers. APIs that require browser cookies, specific User-Agent headers, or JavaScript execution will not work from validator nodes on testnet.

**Suggestion for GenLayer team:**
Consider documenting a list of confirmed compatible APIs for developers. A curated compatibility list would save significant development time.

---

### 2. `gl.message.sender_account` Renamed to `gl.message.sender_address`

The caller identity property was renamed from `gl.message.sender_account` to `gl.message.sender_address` in a SDK update. The old property name silently fails — returning no data without any error or deprecation warning. Older examples and community tutorials still reference `sender_account`, causing developers to believe the feature is broken when they are simply using the outdated name.

**What works:**
The current property `gl.message.sender_address` functions correctly. The GenLayer storage documentation (docs.genlayer.com/developers/intelligent-contracts/storage) demonstrates its use: `self.minter = gl.message.sender_address`.

**Impact:**
During development of the Key Vault contract, the older name `gl.message.sender_account` was used based on earlier examples. It silently returned no data, making it appear that caller identity verification was broken on the platform. Hours were spent debugging before discovering the rename. The workaround — requiring callers to pass their wallet address as a parameter — was implemented unnecessarily.

**Suggested fix:**
Add a migration note in the Messages documentation flagging the rename. Implement a runtime deprecation warning when `sender_account` is accessed, directing developers to use `sender_address` instead. Update or annotate all older example contracts that still reference the old name.

---

### 3. `assert` Statements Do Not Always Revert Transactions

On GenLayer Studio, a failed `assert` statement sometimes did not stop transaction execution. Transactions finalized as ACCEPTED even when the assertion condition was false, meaning certain validation checks did not behave as expected.

**Recommended alternative:**
The GenLayer docs recommend using `raise gl.vm.UserError("message")` instead of `assert` for error handling. This preserves the error message in the transaction receipt and is designed for reliable transaction reversion.

**Workaround used:**
Error messages were stored directly in contract state instead of relying on transaction reverts. Developers can read errors via `get_last_response()` or `get_audit_log()`.

---

### 4. `strict_eq` Fails for Live Data

`eq_principle.strict_eq` requires all five validators to return the exact same result. For live data — crypto prices, weather readings, news stories — each validator fetches at a slightly different moment so values naturally differ. This caused multiple UNDETERMINED outcomes during early testing.

**Workaround used:**
Switched to `eq_principle.prompt_comparative` with a defined tolerance range. This allows validators to agree on results that are close enough rather than requiring identical outputs. For example, crypto prices within 2% of each other are considered equivalent.

**Recommended approach from docs:**
For numerical comparisons (prices, temperatures, percentages), the GenLayer docs recommend `gl.vm.run_nondet_unsafe` with a custom validator function that calculates tolerance in Python code — faster and more precise than asking an LLM to judge equivalence. `prompt_comparative` is best reserved for subjective text comparisons (summaries, analysis) where LLM judgment genuinely adds value.

---

## Summary

| Issue | Type | Priority |
|---|---|---|
| Schema error — no detail | UX | High |
| Array input — no format hint | UX | High |
| JSON response — raw display | UX | Medium |
| UNDETERMINED — no explanation | UX | High |
| Simulation Mode — easy to miss | UX | High |
| Upgrade code — no confirmation | UX | Medium |
| Read methods — no auto-refresh | UX | Medium |
| APIs blocking validators | Limitation | High |
| `gl.message.sender_account` renamed | Limitation | High — silent failure, needs deprecation warning |
| `assert` not reverting | Limitation | Medium — use `gl.vm.UserError` as alternative |
| `strict_eq` fails for live data | Limitation | High — use `run_nondet_unsafe` or `prompt_comparative` |