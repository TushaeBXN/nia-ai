"""
Web Search Tool — live research for Nia's squad agents.

Uses DuckDuckGo (no API key needed) with an HTML scrape fallback.
Returns structured results the agents can reason over.

Usage:
    python -m tools.web_search "CFPB complaint Capital One"
    python -m tools.web_search "statute of limitations credit card debt Texas"
    python -m tools.web_search "is ABC Collections licensed in North Carolina"
"""

import sys
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MAX_RESULTS = 5
TIMEOUT = 10


def _ddg_search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """DuckDuckGo instant answer API — no key required."""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "source": "duckduckgo",
                })
        return results
    except ImportError:
        return []
    except Exception:
        return []


def _html_fallback(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """HTML scrape of DuckDuckGo search page — no library required."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract result blocks
        results = []
        # Find all result titles and snippets
        title_pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<', re.IGNORECASE
        )
        snippet_pattern = re.compile(
            r'class="result__snippet"[^>]*>([^<]+)<', re.IGNORECASE
        )

        titles = title_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (url_raw, title) in enumerate(titles[:max_results]):
            # DDG redirect URLs — extract actual URL
            actual_url = url_raw
            if "uddg=" in url_raw:
                try:
                    actual_url = urllib.parse.unquote(
                        url_raw.split("uddg=")[1].split("&")[0]
                    )
                except Exception:
                    pass
            results.append({
                "title": title.strip(),
                "url": actual_url,
                "snippet": snippets[i].strip() if i < len(snippets) else "",
                "source": "ddg-html",
            })
        return results
    except Exception:
        return []


def search(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """
    Search the web. Returns list of {title, url, snippet, source}.
    Tries duckduckgo_search library first, falls back to HTML scrape.
    """
    results = _ddg_search(query, max_results)
    if not results:
        results = _html_fallback(query, max_results)
    return results


# ── Nia-specific search helpers ───────────────────────────────────────────────

def search_cfpb_complaints(company: str) -> list[dict]:
    """Search CFPB complaint database for a company."""
    query = f"CFPB complaint {company} site:consumerfinance.gov OR site:cfpb.gov"
    results = search(query, max_results=3)
    # Also try the CFPB API
    try:
        encoded = urllib.parse.quote_plus(company)
        api_url = (
            f"https://api.consumerfinance.gov/data/complaints"
            f"?company={encoded}&format=json&size=3&sort=created_date_desc"
        )
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
        hits = data.get("hits", {}).get("hits", [])
        for hit in hits[:3]:
            src = hit.get("_source", {})
            results.insert(0, {
                "title": f"CFPB Complaint — {src.get('company', company)}",
                "url": "https://www.consumerfinance.gov/data-research/consumer-complaints/",
                "snippet": (
                    f"Product: {src.get('product', 'N/A')} | "
                    f"Issue: {src.get('issue', 'N/A')} | "
                    f"Date: {src.get('date_received', 'N/A')} | "
                    f"Company response: {src.get('company_response', 'N/A')}"
                ),
                "source": "cfpb-api",
            })
    except Exception:
        pass
    return results


def search_collector_license(collector: str, state: str) -> list[dict]:
    """Check if a debt collector is licensed in a state."""
    queries = [
        f'"{collector}" debt collector license {state}',
        f'"{collector}" collection agency license {state} secretary of state',
        f'site:nmlsconsumeraccess.org "{collector}"',
    ]
    results = []
    for q in queries[:2]:
        results.extend(search(q, max_results=2))
    return results[:4]


def search_credit_news(topic: str) -> list[dict]:
    """Search for recent news on a credit/financial topic."""
    query = f"{topic} 2025 OR 2026 site:cfpb.gov OR site:ftc.gov OR site:nerdwallet.com OR site:creditkarma.com"
    return search(query, max_results=4)


def search_for_profit_school(school: str) -> list[dict]:
    """Check if a for-profit school qualifies for loan discharge."""
    queries = [
        f'"{school}" borrower defense loan discharge',
        f'"{school}" closed school discharge student loan',
        f'"{school}" department of education settlement',
    ]
    results = []
    for q in queries:
        results.extend(search(q, max_results=2))
    return results[:5]


def format_results(results: list[dict], query: str = "") -> str:
    """Format search results for Nia's agents."""
    if not results:
        return f"No results found for: {query}"

    lines = [f"── WEB SEARCH: {query} ─────────────────────────────"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet'][:200]}")
    lines.append("\n────────────────────────────────────────────────────")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    query = " ".join(args)

    # Special modes
    if "--cfpb" in args:
        company = " ".join(a for a in args if not a.startswith("--"))
        results = search_cfpb_complaints(company)
    elif "--collector" in args and "--state" in args:
        idx_c = args.index("--collector")
        idx_s = args.index("--state")
        collector = args[idx_c + 1]
        state = args[idx_s + 1]
        results = search_collector_license(collector, state)
        query = f"{collector} license in {state}"
    elif "--school" in args:
        school = " ".join(a for a in args if not a.startswith("--"))
        results = search_for_profit_school(school)
    else:
        results = search(query)

    print(format_results(results, query))


if __name__ == "__main__":
    main()
