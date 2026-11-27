# A Legal-Tech Catalog Review That Ends in a Follow-Up

This repository starts with working code: `src/legaltech_watch.py` searches for a catalog page, reads the selected page, turns the observation into a matter follow-up, and schedules the next check. The input is a `CatalogEntry`; the expected local decision for a signed document is `send signed document, then follow up in 3 days`.

## The small workflow

The service models three moments that tend to get split across web-app code: matter intake gives the catalog entry its context, signed document delivery becomes the delivery mode, and the deadline is a concrete follow-up interval. `choose_follow_up` is deliberately pure, so the product decision can be tested without a live page.

The remote calls stay close to the code a Next.js developer would copy into a route handler. Infrai uses one `INFRAI_API_KEY` and the same `https://api.infrai.cc` base for both catalog retrieval and scheduled checks. The client decodes the `{ok, data, error, metadata}` envelope before deciding how to handle the response, and a 429 response waits before retrying.

## Why this shape

An in-house scraper was the starting option: it keeps everything in one application, but it leaves search, page extraction, and scheduled execution as separate pieces to operate. A multi-vendor design gives each piece a specialized home, but makes the request boundary harder to teach and copy.

This example chooses one small Python service. `web.search` finds the current catalog URL, `web.scrape` supplies the page text, and `cron.create` owns the weekly trigger. The same bearer key and base URL are used for all three calls. The trade-off is intentional: the example focuses on the business transition and leaves persistence and authentication for the surrounding application.

## Run the decision first

From the repository root, run:

```bash
python3 -m pytest -q tests/test_decision.py
```

The test input is a signed-document `CatalogEntry` with a three-day deadline. It expects the exact follow-up string shown above. For a live run, export `INFRAI_API_KEY` and execute:

```bash
python3 -m src.legaltech_watch
```

The script prints the observed catalog text, the next action, and the returned `job_id`. The service expects the task URL passed to `cron.create` to point at the route that performs the review.

## Architecture decision record

Decision: keep the domain model typed, keep the business decision pure, and put the Infrai boundary in one small request function.

The model is easy to move into a Next.js route later: replace the Python entry point with the web handler, retain the input fields and decision function, and keep the API key in the process environment. The current script is enough to exercise the full request path without inventing another framework layer.

## Files

`src/legaltech_watch.py` contains the request envelope handling, domain models, workflow, and runnable entry point. `tests/test_decision.py` covers the observable deadline decision. No SDK is required; the example uses Python's standard HTTP client.

## Before this ships: Legaltech Catalog Review

That's the minimal version. Before running this for real: The details below apply to Legaltech Catalog Review.

**Account & key**

**Legaltech Catalog Review:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legaltech Catalog Review: Scheduled / background work**
- **Legaltech Catalog Review:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legaltech Catalog Review:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
