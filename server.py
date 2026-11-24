from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from verifier import KeyRecord, ReceiptVerifier


def load_keys() -> dict[str, KeyRecord]:
    raw = os.getenv("STATEPROOF_PUBLIC_KEYS_JSON", "{}")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("STATEPROOF_PUBLIC_KEYS_JSON must be a JSON object")
    result: dict[str, KeyRecord] = {}
    for key_id, encoded in data.items():
        import base64
        padded = encoded + "=" * (-len(encoded) % 4)
        result[key_id] = KeyRecord(Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(padded)))
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "StateProofVerifier/0.1"

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._json(200, {"status": "ok", "service": "stateproof-verifier"})
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/verify":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 2_000_000:
                raise ValueError("request body must be between 1 byte and 2 MB")
            payload = json.loads(self.rfile.read(length))
            receipt = payload.get("receipt") if isinstance(payload, dict) else None
            if not isinstance(receipt, dict):
                raise ValueError("body must contain a receipt object")
            result = ReceiptVerifier(load_keys()).verify(receipt)
            self._json(200, result)
        except Exception as exc:
            self._json(400, {"verification": "REJECTED", "reason": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep Railway logs concise and avoid logging receipt contents.
        print("stateproof", fmt % args)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
