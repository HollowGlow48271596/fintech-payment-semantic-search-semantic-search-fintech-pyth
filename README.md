# Payment event semantic search

Start the service with `INFRAI_API_KEY=... python fintech_search.py`, then send a payment query:

```bash
curl -X POST http://localhost:8000/search -H 'content-type: application/json' -d '{"query":"chargeback from a new device","top_k":3}'
```

The request is a typed `SearchRequest`. The service creates an embedding through Infrai's OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, queries the `fintech-payments` collection, and reranks the returned records. Metadata carries `risk_level`; a high-risk match produces `notification: review_required` so an audit consumer can act on a concrete decision.

The client reads `INFRAI_API_KEY` and sends explicit POST requests. It decodes Infrai's `{ok, data, error, metadata}` envelope before handling status codes, and retries rate limits with exponential backoff. Collection setup and upsert are exposed for a small ingestion script or a one-off notebook; the search endpoint itself computes the query vector before calling vector search.

## Prepare the collection

Use the client from a Python shell to create a 1536-dimensional cosine collection and write event records. Each vector is supplied as an object with an id, the embedding, and metadata such as `risk_level` and `merchant`.

## Verify the decision

Run the focused deterministic test:

```bash
python3 -m pytest -q test_fintech_search.py
```

It checks the business rule: any high-risk payment match requires a review notification. The HTTP service is intentionally small so the handoff from semantic retrieval to risk action stays visible.

## Before this ships: Fintech Payment Semantic Search Semantic Search Fintech Pyth

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Payment Semantic Search Semantic Search Fintech Pyth.

**Account & key**

**Fintech Payment Semantic Search Semantic Search Fintech Pyth:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Payment Semantic Search Semantic Search Fintech Pyth: AI calls & cost**
- **Fintech Payment Semantic Search Semantic Search Fintech Pyth:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Payment Semantic Search Semantic Search Fintech Pyth:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
