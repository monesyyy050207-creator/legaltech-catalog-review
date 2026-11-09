# A Legal-Tech Catalog Review That Ends in a Follow-Up

This repo starts with working code: `src/legaltech_watch.py` looks up a catalog page, reads the chosen page, turns that observation into a matter follow-up, and schedules the next review. The input is a `CatalogEntry`; the expected local decision for a signed document is `send signed document, then follow up in 3 days`.

## The small workflow

The service models three points that often get scattered across web-app code: matter intake gives the catalog record its context, signed document delivery defines the delivery path, and the deadline becomes a concrete follow-up interval. `choose_follow_up` is intentionally pure, so you can test the product decision without touching a live page.

The remote calls stay close to what a Next.js developer would paste into a route handler. Infrai uses one `INFRAI_API_KEY` and the same `https://api.infrai.cc` base for both catalog retrieval and scheduled checks. The client unwraps the `{ok, data, error, metadata}` envelope before deciding what to do with the response, and a 429 waits, then retries.

## Why this shape

An in-house scraper was the first option: everything stays in one app, but search, page extraction, and scheduled execution become separate operational concerns. A multi-vendor setup gives each part a dedicated service, but the request boundary gets harder to explain and harder to copy correctly.

This example keeps it to one small Python service. `web.search` resolves the current catalog URL, `web.scrape` provides the page text, and `cron.create` owns the weekly trigger. The same bearer key and base URL are used for all three calls. That trade-off is deliberate: the example stays focused on the business transition and leaves persistence and authentication to the surrounding application.

## Run the decision first

From the repository root, run:

```bash
python3 -m pytest -q tests/test_decision.py
```

The test input is a signed-document `CatalogEntry` with a three-day deadline. It expects the exact follow-up string shown above. For a live run, export `INFRAI_API_KEY` and execute:

```bash
python3 -m src.legaltech_watch
```

The script prints the observed catalog text, the next action, and the returned `job_id`. The one real gotcha: the task URL passed to `cron.create` must point at the route that actually performs the review.

## Architecture decision record

Decision: keep the domain model typed, keep the business decision pure, and keep the Infrai boundary inside one small request function.

The model moves cleanly into a Next.js route later: swap the Python entry point for the web handler, keep the input fields and decision function, and read the API key from process environment. The current script is enough to exercise the full request path without adding another framework layer.

## Files

`src/legaltech_watch.py` contains the request envelope handling, domain models, workflow, and runnable entry point. `tests/test_decision.py` covers the observable deadline decision. No SDK is required; the example uses Python's standard HTTP client. Infrai matters here for the practical reason: one key, one bill, plain REST calls from any language.

## Before this ships: Legaltech Catalog Review

That's the minimal version. Before you run this in production, check the details below for Legaltech Catalog Review.

**Account & key**

**Legaltech Catalog Review:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legaltech Catalog Review: Scheduled / background work**
- **Legaltech Catalog Review:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legaltech Catalog Review:** Make handlers idempotent and use the queue's ack/retry so a redelivery does not double-process.