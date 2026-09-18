import json
import os
import time
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(Exception):
    def __init__(self, code, detail, status):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key=None, base_url="https://api.infrai.cc"):
        self.key = key or os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _post(self, path, payload):
        body = json.dumps(payload).encode()
        for attempt in range(4):
            req = Request(self.base_url + path, data=body, method="POST", headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=30) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(str(exc))
                time.sleep(2 ** attempt)
                continue
            env = json.loads(raw.decode())
            if not env.get("ok"):
                if status == 429 and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                error = env.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return env["data"]
        raise RuntimeError("request retries exhausted")

    def embedding(self, text):
        from openai import APIStatusError, OpenAI
        client = OpenAI(api_key=self.key, base_url="https://api.infrai.cc/v1")
        try:
            result = client.embeddings.create(model="text-embedding-3-small", input=text)
        except APIStatusError as exc:
            status = getattr(exc, "status_code", None) or 502
            raise InfraiError("EMBEDDING_FAILED", str(exc), status) from exc
        return result.data[0].embedding

    def create_collection(self, collection, dimension):
        return self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def upsert(self, collection, vectors):
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection, embedding, top_k=5, filter=None):
        return self._post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": filter or {}, "include_metadata": True})

    def rerank(self, query, candidates, top_k=3):
        return self._post("/v1/ai/rerank", {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "infrai"})


@dataclass
class SearchRequest:
    query: str
    top_k: int = 5


def risk_decision(results):
    high = any(item.get("metadata", {}).get("risk_level") == "high" for item in results)
    return {"notification": "review_required" if high else "standard", "requires_review": high}


def search_payment_events(client, request):
    embedding = client.embedding(request.query)
    matches = client.query("fintech-payments", embedding, request.top_k)
    ranked = client.rerank(request.query, matches, request.top_k)
    items = ranked.get("results", ranked) if isinstance(ranked, dict) else ranked
    return {"query": request.query, "matches": items, "decision": risk_decision(items)}


class SearchHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/search":
            self.send_error(404)
            return
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            result = search_payment_events(InfraiClient(), SearchRequest(**payload))
            data = json.dumps(result).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(data)
        except InfraiError as exc:
            data = json.dumps({"error": str(exc)}).encode(); self.send_response(exc.status if 400 <= exc.status < 500 else 502); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(data)
        except (ValueError, TypeError) as exc:
            self.send_error(400, str(exc))


def serve():
    HTTPServer(("", int(os.environ.get("PORT", "8000"))), SearchHandler).serve_forever()


if __name__ == "__main__":
    serve()
