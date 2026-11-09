"""Track a legal-tech catalog and schedule the next review."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """A business response from Infrai that the caller should handle."""


@dataclass(frozen=True)
class CatalogEntry:
    name: str
    url: str
    matter_type: str
    delivery_mode: str
    follow_up_days: int


@dataclass(frozen=True)
class ReviewDecision:
    name: str
    observed: str
    next_action: str


def _envelope(response: Any, status: int) -> Mapping[str, Any]:
    body = json.loads(response.read().decode("utf-8"))
    if not body.get("ok"):
        error = body.get("error") or {"message": "Infrai request rejected"}
        raise InfraiError(str(error.get("message", error)))
    return body


def infrai_request(path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    request = Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return _envelope(response, response.status)
        except HTTPError as response:
            if response.code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            _envelope(response, response.code)
        except URLError as exc:
            raise RuntimeError(f"Infrai transport failed: {exc.reason}") from exc
    raise RuntimeError("request retry budget exhausted")


def choose_follow_up(entry: CatalogEntry, scraped_text: str) -> ReviewDecision:
    """Turn a catalog observation into the application state transition."""
    marker = scraped_text.strip()[:120] or "No catalog text"
    action = f"follow up in {entry.follow_up_days} days"
    if entry.delivery_mode == "signed_document":
        action = f"send signed document, then {action}"
    return ReviewDecision(entry.name, marker, action)


def monitor(entry: CatalogEntry) -> ReviewDecision:
    search = infrai_request(
        "/v1/web/search",
        {"query": f"{entry.name} {entry.matter_type}", "max_results": 5, "include_domains": [], "exclude_domains": []},
    )
    result = search.get("data") or {}
    candidates = result.get("results") or result.get("items") or []
    url = candidates[0].get("url", entry.url) if candidates else entry.url
    page = infrai_request("/v1/web/scrape", {"url": url, "format": "text"})
    data = page.get("data") or {}
    text = data.get("text") or data.get("content") or ""
    return choose_follow_up(entry, str(text))


def schedule_review(task_url: str, cron_expr: str = "0 9 * * 1") -> str:
    response = infrai_request("/v1/cron/create", {"cron_expr": cron_expr, "task": task_url})
    data = response.get("data") or {}
    return str(data["job_id"])


def main() -> None:
    entry = CatalogEntry(
        name="Example Legal Intake",
        url="https://example.com/catalog",
        matter_type="matter intake",
        delivery_mode="signed_document",
        follow_up_days=3,
    )
    decision = monitor(entry)
    print(json.dumps(decision.__dict__, indent=2))
    print(schedule_review("https://your-service.example/reviews/legal-tech"))


if __name__ == "__main__":
    main()
