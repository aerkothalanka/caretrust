from __future__ import annotations

import asyncio
import json
import os
import re
from html.parser import HTMLParser
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import Facility

MAX_CRAWL_CHARS = 18_000
MAX_URLS = 3
DEFAULT_TIMEOUT_SECONDS = 15


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text)


def source_urls_for_facility(facility: Facility) -> list[str]:
    raw: list[Any] = []
    for value in [facility.source_url, facility.website, facility.source_row.get("source_urls"), facility.source_row.get("websites")]:
        if not value:
            continue
        if isinstance(value, list):
            raw.extend(value)
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                raw.extend(parsed if isinstance(parsed, list) else [value])
            except Exception:
                raw.extend(re.split(r"[,;\s]+", value))
    seen: set[str] = set()
    urls: list[str] = []
    for item in raw:
        url = str(item or "").strip().strip("'\"")
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        if not parsed.netloc or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls[:MAX_URLS]


def verify_trust_sources(facility: Facility, procedure: str, service_label: str, mode: str = "crawl") -> dict[str, Any]:
    urls = source_urls_for_facility(facility)
    crawls = [_crawl_source(url) for url in urls]
    checks = [_score_source(facility, service_label, crawl) for crawl in crawls]
    verified = sum(1 for item in checks if item["status"] == "verified")
    partial = sum(1 for item in checks if item["status"] == "partial")
    failed = sum(1 for item in checks if item["status"] in {"failed", "unreachable"})
    status = "verified" if verified else "partial" if partial else "needs_review" if checks else "no_sources"
    summary = _summary_for(status, checks, service_label)
    agent = _agent_bricks_review(facility, procedure, service_label, checks) if mode == "agent" else None
    return {
        "facility_id": facility.unique_id,
        "facility_name": facility.name,
        "procedure": procedure,
        "service_label": service_label,
        "mode": mode,
        "status": status,
        "summary": summary,
        "source_count": len(urls),
        "verified_count": verified,
        "partial_count": partial,
        "failed_count": failed,
        "checks": checks,
        "agent_bricks": agent,
    }


def _crawl_source(url: str) -> dict[str, Any]:
    try:
        markdown = asyncio.run(_crawl4ai_markdown(url))
        if markdown:
            return {"url": url, "ok": True, "crawler": "crawl4ai", "markdown": markdown[:MAX_CRAWL_CHARS]}
    except Exception as exc:
        crawl4ai_error = f"{type(exc).__name__}: {exc}"
    else:
        crawl4ai_error = "Crawl4AI returned no markdown"

    fallback = _fallback_text_fetch(url)
    fallback["crawl4ai_error"] = crawl4ai_error
    return fallback


async def _crawl4ai_markdown(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig  # type: ignore

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=DEFAULT_TIMEOUT_SECONDS * 1000)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
    markdown = getattr(result, "markdown", None) or getattr(result, "cleaned_html", None) or ""
    return str(markdown)


def _fallback_text_fetch(url: str) -> dict[str, Any]:
    try:
        req = Request(url, headers={"User-Agent": "CareSignal Trust Verifier/1.0"})
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            raw = resp.read(350_000)
            content_type = resp.headers.get("content-type", "")
        text = raw.decode("utf-8", errors="ignore")
        if "html" in content_type.lower() or "<html" in text[:500].lower():
            parser = _TextExtractor()
            parser.feed(text)
            text = "\n".join(parser.parts)
        return {"url": url, "ok": True, "crawler": "fallback-http", "markdown": text[:MAX_CRAWL_CHARS]}
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {"url": url, "ok": False, "crawler": "fallback-http", "markdown": "", "error": f"{type(exc).__name__}: {exc}"}


def _score_source(facility: Facility, service_label: str, crawl: dict[str, Any]) -> dict[str, Any]:
    text = str(crawl.get("markdown") or "")
    lower = text.lower()
    facility_tokens = [token for token in re.split(r"\W+", facility.name.lower()) if len(token) >= 4]
    facility_hits = [token for token in facility_tokens[:8] if token in lower]
    service_terms = _terms_for(service_label) + _terms_for(" ".join(facility.procedures or [])) + _terms_for(" ".join(facility.specialties or []))
    evidence_terms = _terms_for(" ".join((facility.equipment or []) + (facility.capabilities or [])))
    service_hits = [term for term in service_terms if term in lower][:8]
    evidence_hits = [term for term in evidence_terms if term in lower][:8]
    if not crawl.get("ok"):
        status = "unreachable"
    elif facility_hits and (service_hits or evidence_hits):
        status = "verified"
    elif facility_hits or service_hits or evidence_hits:
        status = "partial"
    else:
        status = "needs_review"
    excerpt = _best_excerpt(text, facility_hits + service_hits + evidence_hits)
    return {
        "url": crawl.get("url"),
        "status": status,
        "crawler": crawl.get("crawler"),
        "facility_hits": facility_hits,
        "service_hits": service_hits,
        "evidence_hits": evidence_hits,
        "excerpt": excerpt,
        "error": crawl.get("error") or crawl.get("crawl4ai_error"),
    }


def _terms_for(value: str) -> list[str]:
    raw = re.split(r"[,;/|()\[\]\-]+|\s+", str(value or "").lower())
    skip = {"and", "the", "for", "with", "care", "service", "services", "surgery", "hospital"}
    terms = []
    for term in raw:
        term = re.sub(r"[^a-z0-9]+", "", term)
        if len(term) >= 4 and term not in skip and term not in terms:
            terms.append(term)
    return terms[:14]


def _best_excerpt(text: str, terms: list[str]) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    lower = compact.lower()
    positions = [lower.find(term.lower()) for term in terms if term and lower.find(term.lower()) >= 0]
    start = max(0, min(positions) - 120) if positions else 0
    return compact[start : start + 360]


def _summary_for(status: str, checks: list[dict[str, Any]], service_label: str) -> str:
    if status == "verified":
        return f"Crawled source links support the {service_label} trust claim. Review excerpts before final referral."
    if status == "partial":
        return f"Crawled sources partially support the {service_label} claim; use human review for missing details."
    if status == "no_sources":
        return "No source links were available on this Trust Card."
    failed = sum(1 for check in checks if check.get("status") == "unreachable")
    if failed and failed == len(checks):
        return "Source links could not be reached from the app runtime. Confirm manually or retry later."
    return f"Crawled sources did not clearly support the {service_label} claim. Mark for review before referral."


def _agent_bricks_review(facility: Facility, procedure: str, service_label: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    endpoint = os.getenv("CARESIGNAL_AGENT_BRICKS_ENDPOINT") or os.getenv("CARESIGNAL_AGENT_BRICKS_ENDPOINT_NAME")
    if not endpoint:
        return {
            "enabled": False,
            "status": "not_configured",
            "summary": "Set CARESIGNAL_AGENT_BRICKS_ENDPOINT to route crawled evidence through an Agent Bricks serving endpoint.",
        }
    prompt = _agent_prompt(facility, procedure, service_label, checks)
    try:
        from databricks.sdk import WorkspaceClient

        client = WorkspaceClient()
        bodies = [
            # Agent Bricks / Mosaic Agent Serving endpoints commonly expose an agent/v1/responses-style task.
            {"input": [{"role": "user", "content": prompt}]},
            {"input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]},
            # Foundation/chat serving endpoints accept OpenAI-compatible chat messages.
            {
                "messages": [
                    {"role": "system", "content": "You verify healthcare facility trust-card claims from crawled website evidence. Be concise and cite gaps."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 500,
            },
        ]
        errors: list[str] = []
        for body in bodies:
            try:
                data = client.api_client.do("POST", f"/serving-endpoints/{endpoint}/invocations", body=body)
                text = _extract_agent_text(data if isinstance(data, dict) else {"response": data})
                return {"enabled": True, "status": "ok", "endpoint": endpoint, "summary": text or json.dumps(data, default=str)[:1200]}
            except Exception as exc:  # try the alternate endpoint shape before surfacing the error
                errors.append(f"{type(exc).__name__}: {exc}")
        return {"enabled": True, "status": "error", "endpoint": endpoint, "summary": "Agent Bricks query failed: " + " | ".join(errors[-2:])}
    except Exception as exc:
        return {"enabled": True, "status": "error", "endpoint": endpoint, "summary": f"Agent Bricks client setup failed: {type(exc).__name__}: {exc}"}


def _agent_prompt(facility: Facility, procedure: str, service_label: str, checks: list[dict[str, Any]]) -> str:
    evidence = [
        {
            "url": check.get("url"),
            "status": check.get("status"),
            "facility_hits": check.get("facility_hits"),
            "service_hits": check.get("service_hits"),
            "evidence_hits": check.get("evidence_hits"),
            "excerpt": check.get("excerpt"),
        }
        for check in checks
    ]
    payload = {
        "facility": facility.name,
        "location": ", ".join([x for x in [facility.city, facility.state, facility.pincode] if x]),
        "procedure": procedure,
        "service_label": service_label,
        "trust_claim": f"Facility supports {service_label}",
        "crawled_evidence": evidence,
    }
    return "Return JSON with verdict verified|partial|needs_review, rationale, and follow_up_questions. Evidence packet:\n" + json.dumps(payload, ensure_ascii=False)


def _extract_agent_text(data: dict[str, Any]) -> str:
    try:
        if data.get("output_text"):
            return str(data["output_text"])
        if data.get("response"):
            return str(data["response"])
        output = data.get("output") or []
        if isinstance(output, list):
            texts: list[str] = []
            for item in output:
                if isinstance(item, dict):
                    for content in item.get("content", []) or []:
                        if isinstance(content, dict) and content.get("text"):
                            texts.append(str(content["text"]))
                    if item.get("text"):
                        texts.append(str(item["text"]))
            if texts:
                return "\n".join(texts)
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            return str(message.get("content") or choices[0].get("text") or "")
        predictions = data.get("predictions") or data.get("outputs") or []
        if predictions:
            first = predictions[0]
            if isinstance(first, dict):
                return str(first.get("content") or first.get("text") or first.get("answer") or first)
            return str(first)
    except Exception:
        return ""
    return ""
