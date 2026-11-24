import re

import httpx

from app.backends import call_local

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def web_search(query: str, max_results: int = 4) -> list[dict]:
    """Free, keyless fact lookup against Wikipedia. No bot-blocking, unlike
    scraping a general search engine from a datacenter IP."""
    try:
        resp = httpx.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
            },
            headers={"User-Agent": "TrinityAI-Gateway/1.0 (self-hosted; contact: app owner)"},
            timeout=15,
        )
        resp.raise_for_status()
        hits = resp.json().get("query", {}).get("search", [])
        return [
            {
                "body": _strip_html(h.get("snippet", "")),
                "href": f"https://en.wikipedia.org/wiki/{h.get('title', '').replace(' ', '_')}",
            }
            for h in hits
        ]
    except Exception:
        return []


def verify_claim(claim: str) -> tuple[str, str, list[str]]:
    """Returns (verdict, confidence, sources). verdict in confirmed/contradicted/unconfirmed."""
    results = web_search(claim, max_results=6)
    if len(results) < 2:
        return "unconfirmed", "low", [r.get("href", "") for r in results]

    snippets = "\n\n".join(f"- {r.get('body', '')} (source: {r.get('href', '')})" for r in results)
    sources = [r.get("href", "") for r in results if r.get("href")]

    judge_prompt = [
        {
            "role": "system",
            "content": (
                "You fact-check a single claim against search results from Wikipedia, "
                "a crowd-edited source that is usually right but can be wrong or vandalized. "
                "Be conservative: reply CONFIRMED only if at least two distinct results "
                "independently support the claim. If only one result supports it, or the "
                "results disagree with each other, reply UNCONFIRMED. If the results clearly "
                "contradict the claim, reply CONTRADICTED. "
                "Reply with exactly one word first: CONFIRMED, CONTRADICTED, or UNCONFIRMED, "
                "then a short reason on the next line."
            ),
        },
        {
            "role": "user",
            "content": f"Claim: {claim}\n\nSearch results:\n{snippets}\n\nVerdict?",
        },
    ]

    try:
        reply = call_local(judge_prompt, max_tokens=200)
    except Exception:
        return "unconfirmed", "low", sources

    first_word = reply.strip().split()[0].upper().strip(".:") if reply.strip() else "UNCONFIRMED"
    if first_word == "CONFIRMED":
        return "confirmed", "high", sources
    if first_word == "CONTRADICTED":
        return "contradicted", "high", sources
    return "unconfirmed", "medium", sources
