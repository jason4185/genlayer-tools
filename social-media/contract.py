# { "Depends": "py-genlayer:test" }

# ═══════════════════════════════════════════════════════════
#  GenLayer Social Media Library — Tools & Infrastructure
#  Fetches live Hacker News data on-chain.
#  No API key required. Fully open public API.
#
#  DEVELOPER QUICKSTART:
#  ┌─────────────────────────────────────────────────────┐
#  │  get_top_stories()           → fetch top 10 stories │
#  │  get_new_stories()           → fetch 10 newest      │
#  │  get_best_stories()          → fetch 10 best        │
#  │  get_most_commented()        → highest comments     │
#  │  get_summary()               → AI news summary      │
#  │  search_cached(keyword)      → search by keyword    │
#  │  is_cache_stale()            → check data freshness │
#  │  get_last_updated()          → last fetch time      │
#  │  get_cached("top")           → free read            │
#  │  get_all()                   → all cached           │
#  └─────────────────────────────────────────────────────┘
# ═══════════════════════════════════════════════════════════

from genlayer import *
import json
import typing

HN_BASE = "https://hacker-news.firebaseio.com/v0"


def fetch_stories(category: str, limit: int = 10) -> str:
    """Helper that fetches stories and handles API errors gracefully."""
    try:
        ids_raw = gl.nondet.web.render(
            f"{HN_BASE}/{category}stories.json",
            mode="text"
        )

        if not ids_raw or ids_raw.strip() in ["null", "", "null\n"]:
            return json.dumps({
                "error": "Hacker News API is down. Please try again later.",
                "status": "unavailable"
            })

        ids = json.loads(ids_raw)

        if not isinstance(ids, list) or len(ids) == 0:
            return json.dumps({
                "error": "Hacker News API is down. Please try again later.",
                "status": "unavailable"
            })

        stories = []
        for story_id in ids[:limit]:
            story_raw = gl.nondet.web.render(
                f"{HN_BASE}/item/{story_id}.json",
                mode="text"
            )

            if not story_raw or story_raw.strip() == "null":
                continue

            s = json.loads(story_raw)
            if not s:
                continue

            stories.append({
                "id":       s.get("id"),
                "title":    s.get("title", "No title"),
                "score":    s.get("score", 0),
                "comments": s.get("descendants", 0),
                "url":      s.get("url", ""),
                "author":   s.get("by", "unknown"),
            })

        if len(stories) == 0:
            return json.dumps({
                "error": "Hacker News API is down. Please try again later.",
                "status": "unavailable"
            })

        return json.dumps({
            "source":      "Hacker News",
            "category":    category,
            "story_count": len(stories),
            "status":      "ok",
            "stories":     stories,
        }, sort_keys=True)

    except Exception:
        return json.dumps({
            "error": "Hacker News API is down. Please try again later.",
            "status": "unavailable"
        })


class SocialMediaOracle(gl.Contract):

    cache:        str  # stores all story data
    last_updated: str  # timestamp of last successful fetch

    def __init__(self):
        self.cache        = "{}"
        self.last_updated = "never"

    @gl.public.write
    def get_top_stories(self) -> typing.Any:
        """Fetch top 10 stories from Hacker News and cache on-chain."""

        def fetch() -> str:
            return fetch_stories("top", 10)

        fresh = gl.eq_principle.prompt_comparative(
            fetch,
            "The outputs represent top stories from Hacker News. "
            "They are equivalent if both show an API down error, "
            "or if they share at least 3 of the same story titles."
        )

        all_data = json.loads(self.cache)
        all_data["top"] = json.loads(fresh)
        self.cache = json.dumps(all_data, sort_keys=True)
        self.last_updated = "recently"

    @gl.public.write
    def get_new_stories(self) -> typing.Any:
        """Fetch 10 newest stories from Hacker News and cache on-chain."""

        def fetch() -> str:
            return fetch_stories("new", 10)

        fresh = gl.eq_principle.prompt_comparative(
            fetch,
            "The outputs represent new stories from Hacker News. "
            "They are equivalent if both show an API down error, "
            "or if they share at least 2 of the same story titles or IDs."
        )

        all_data = json.loads(self.cache)
        all_data["new"] = json.loads(fresh)
        self.cache = json.dumps(all_data, sort_keys=True)
        self.last_updated = "recently"

    @gl.public.write
    def get_best_stories(self) -> typing.Any:
        """Fetch 10 best stories from Hacker News and cache on-chain."""

        def fetch() -> str:
            return fetch_stories("best", 10)

        fresh = gl.eq_principle.prompt_comparative(
            fetch,
            "The outputs represent best stories from Hacker News. "
            "They are equivalent if both show an API down error, "
            "or if they share at least 3 of the same story titles."
        )

        all_data = json.loads(self.cache)
        all_data["best"] = json.loads(fresh)
        self.cache = json.dumps(all_data, sort_keys=True)
        self.last_updated = "recently"

    @gl.public.write
    def get_summary(self) -> typing.Any:
        """Use LLM to generate a one-line summary of today's top tech news."""
        all_data = json.loads(self.cache)

        if "top" not in all_data:
            return

        titles = [s["title"] for s in all_data["top"].get("stories", [])]

        def summarize() -> str:
            prompt = (
                f"Based on these Hacker News top story titles, write ONE sentence "
                f"summarizing the biggest tech trends right now:\n\n"
                f"{json.dumps(titles)}\n\n"
                f"Respond with only the summary sentence, nothing else."
            )
            return gl.nondet.exec_prompt(prompt)

        summary = gl.eq_principle.prompt_comparative(
            summarize,
            "Both outputs summarize the same tech news trends in one sentence. "
            "They are equivalent if they convey the same main topics."
        )

        all_data["summary"] = summary
        self.cache = json.dumps(all_data, sort_keys=True)

    # ── READ METHODS — free, no transaction needed ──────────────

    @gl.public.view
    def get_cached(self, category: str) -> str:
        """Returns cached stories by category: top, new, or best."""
        all_data = json.loads(self.cache)
        if category in all_data:
            return json.dumps(all_data[category])
        return json.dumps({"error": f"{category} not cached. Call get_top_stories first."})

    @gl.public.view
    def get_all(self) -> str:
        """Returns all cached Hacker News data."""
        return self.cache

    @gl.public.view
    def get_most_commented(self) -> str:
        """Returns the story with the highest comment count from cached top stories."""
        all_data = json.loads(self.cache)
        if "top" not in all_data:
            return json.dumps({"error": "No stories cached. Call get_top_stories first."})

        stories = all_data["top"].get("stories", [])
        if not stories:
            return json.dumps({"error": "No stories available."})

        most_commented = max(stories, key=lambda s: s.get("comments", 0))
        return json.dumps(most_commented)

    @gl.public.view
    def search_cached(self, keyword: str) -> str:
        """Search cached stories by keyword in the title. Case insensitive."""
        all_data = json.loads(self.cache)
        results = []
        keyword_lower = keyword.lower()

        for category in ["top", "new", "best"]:
            if category not in all_data:
                continue
            for story in all_data[category].get("stories", []):
                title = story.get("title", "").lower()
                if keyword_lower in title:
                    story["category"] = category
                    results.append(story)

        if not results:
            return json.dumps({"error": f"No stories found matching '{keyword}'."})

        return json.dumps({"results": results, "count": len(results)})

    @gl.public.view
    def get_last_updated(self) -> str:
        """Returns when the cache was last updated."""
        return self.last_updated

    @gl.public.view
    def is_cache_stale(self) -> str:
        """Returns whether the cache has been populated or not."""
        if self.last_updated == "never":
            return json.dumps({"stale": True, "reason": "Cache has never been populated."})
        return json.dumps({"stale": False, "reason": "Cache has been populated."})