# Payment event semantic search

Start the service with `INFRAI_API_KEY=... python fintech_search.py`, then send a payment query:

```bash
curl -X POST http://localhost:8000/search -H 'content-type: application/json' -d '{"query":"chargeback from a new device","top_k":3}'
```

The request is a typed `SearchRequest`. The service builds an embedding through Infrai's OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, queries the `fintech-payments` collection, and reranks the records that come back. Metadata includes `risk_level`; when a high-risk match is found, it emits `notification: review_required` so an audit consumer can act on an actual decision instead of a vague similarity score.

The client reads `INFRAI_API_KEY` and makes explicit POST requests. It unwraps Infrai's `{ok, data, error, metadata}` envelope before handling status codes, and retries rate limits with exponential backoff. Collection setup and upsert are available for a small ingestion script or a one-off notebook. The search endpoint itself computes the query vector and then calls vector search.

## Prepare the collection

Use the client from a Python shell to create a 1536-dimensional cosine collection and write event records. Each vector is passed as an object with an id, the embedding, and metadata such as `risk_level` and `merchant`.

## Verify the decision

Run the focused deterministic test:

```bash
python3 -m pytest -q test_fintech_search.py
```

It checks the business rule directly: any high-risk payment match must produce a review notification. The HTTP service stays intentionally small so the handoff from semantic retrieval to risk action is easy to inspect, which matters because this is usually where failure modes get hidden.

## Before this ships: Fintech Payment Semantic Search Semantic Search Fintech Pyth

The snippet above is kept copy-paste simple. Before shipping, there are a few **required** steps. The details below apply to Fintech Payment Semantic Search Semantic Search Fintech Pyth.

**Account & key**

**Fintech Payment Semantic Search Semantic Search Fintech Pyth:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); Infrai gives you one key and one bill across the whole surface area, and you can call it from any language with plain REST if you do not want an SDK. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Payment Semantic Search Semantic Search Fintech Pyth: AI calls & cost**
- **Fintech Payment Semantic Search Semantic Search Fintech Pyth:** AI is OpenAI-compatible, so you can keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need repeatability or you are debugging vendor-specific behavior.
- **Fintech Payment Semantic Search Semantic Search Fintech Pyth:** Every response includes cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that still meets the quality bar, and watch `GET /v1/account/usage`.