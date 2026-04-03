# GenLayer Social Media Library

Bring Hacker News on-chain in seconds. No API key. No setup. Just deploy and fetch.

---

## What It Does

This contract pulls live stories from Hacker News directly onto the GenLayer blockchain. Five AI validators fetch and verify the data independently before it gets written on-chain — so what you read is trustless and consensus-backed.

It also ships with a built-in AI summary powered by GenLayer's native LLM access. One call and you get a single sentence telling you what the tech world is talking about right now. No other blockchain can do this.

---

## API

**Hacker News Firebase API**
`https://hacker-news.firebaseio.com/v0`

- Free and open
- No API key
- No rate limits for standard usage
- Returns titles, scores, comments, authors and URLs

---

## Methods

### Fetch (requires a transaction)

| Method | What it does |
|---|---|
| `get_top_stories()` | Top 10 stories right now |
| `get_new_stories()` | 10 newest submissions |
| `get_best_stories()` | 10 highest rated of all time |
| `get_summary()` | AI one-line summary of top tech news |

### Read (free — no transaction)

| Method | What it does |
|---|---|
| `get_all()` | Every cached story at once |
| `get_cached("top")` | Stories by category: top, new, best |
| `get_most_commented()` | Most discussed story in cache |
| `search_cached("AI")` | Search titles by keyword |
| `get_last_updated()` | When cache was last populated |
| `is_cache_stale()` | Check if data needs refreshing |

---

## Response Format

```json
{
  "source": "Hacker News",
  "category": "top",
  "story_count": 10,
  "status": "ok",
  "stories": [
    {
      "id": 47616361,
      "title": "Google releases Gemma 4 open models",
      "score": 1093,
      "comments": 332,
      "url": "https://deepmind.google/models/gemma/gemma-4/",
      "author": "jeffmcjunkin"
    }
  ]
}
```

---

## Error Handling

If Hacker News goes down, you get a clean message — not a broken transaction:

```json
{
  "error": "Hacker News API is down. Please try again later.",
  "status": "unavailable"
}
```

---

## Quick Start

```
1. Paste contract.py into GenLayer Studio
2. Deploy — no arguments needed
3. Call get_top_stories()
4. Call get_all() to read results
```

That's it.

---

## Typical Flow

```
get_top_stories()        → cache 10 stories on-chain
get_summary()            → get AI summary of the news
get_most_commented()     → find what people are debating
search_cached("crypto")  → filter by topic (free)
is_cache_stale()         → know when to refresh (free)
```

---

## License

MIT