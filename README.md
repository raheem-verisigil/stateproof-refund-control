# StateProof Refund Control

StateProof Refund Control is a **customer-controlled transaction-integrity reference implementation** for high-risk, agent- or support-initiated refunds and payment adjustments.

It verifies a bounded claim for a supported connector:

> A defined request was authorized under a named policy, bound to an authoritative pre-state, submitted with retry/concurrency controls, and the authoritative system reported the declared postcondition—or the result remains explicitly unknown, conflicted, or failed.

## What this project is—and is not

This repository is a technical reference implementation and protocol experiment. It is **not** a general agent-observability platform, policy engine, workflow engine, payment processor, provenance standard, or generic AI-security gateway.

StateProof does **not** prove model reasoning, legal compliance, hidden side effects, the truth of a provider's data, or the correctness of a customer's policy. A signature proves the integrity and authorship of a receipt; it does not make an uncorroborated business claim true.

The broad infrastructure market is crowded. The initial validation wedge is **read-only refund outcome reconciliation**: detect ambiguous, conflicting, delayed, or unsupported outcomes across payment, commerce, support, and agent systems before asking a customer to make StateProof the mandatory execution path. The longer-term hypothesis is that selected high-risk workflows will adopt a control path combining provider-specific reconciliation, explicit `UNKNOWN`/`CONFLICT` outcomes, authoritative post-state verification, customer-controlled evidence, and an independently runnable verifier.

## Current status

- Receipt parsing and validation: implemented.
- Ed25519 receipt verification: implemented.
- Canonical signed-body digest checking: implemented as a deterministic JSON profile; replace with a standards-compliant RFC 8785 implementation before cross-language interoperability.
- Replay, expiry, freshness, outcome, and execution-binding checks: implemented.
- Provider-neutral reconciliation loop: implemented as a reference protocol.
- Read-only outcome-reconciliation watcher: roadmap item; no live provider watcher is included yet.
- Automated tests: included and passing locally.
- Live Stripe/Adyen connector: **not included**.
- Durable replay store, KMS/HSM key lifecycle, mTLS/OIDC, tenant isolation, and production deployment controls: **required before live refunds**.

## Quickstart

```bash
python3 -m pip install -e '.[test]'
python3 -m pytest -q
```

The main implementation is in [`verifier.py`](verifier.py). The test suite covers valid signatures, tampering, expiry, replay, invalid-outcome logic, timeout reconciliation, and replay-store poisoning protection.

## Railway demo deployment

This repository includes a minimal read-only HTTP verifier for Railway. It exposes:

- `GET /healthz`
- `POST /verify`

The service does not execute refunds. It verifies receipts against public keys supplied through the `STATEPROOF_PUBLIC_KEYS_JSON` environment variable, encoded as a JSON object mapping key IDs to URL-safe base64 Ed25519 public keys.

Example request:

```bash
curl -X POST "$STATEPROOF_URL/verify" \
  -H 'content-type: application/json' \
  -d '{"receipt": {"...": "..."}}'
```

Do not put private keys, payment credentials, raw payment payloads, or customer PII in Railway environment variables or public issues. For real customer deployments, run the connector and evidence vault inside the customer's approved environment.

## Production hardening required

Before enabling live financial actions:

1. Replace the in-memory replay store with a durable conditional-insert store shared by every verifier instance.
2. Use a standards-compliant RFC 8785/JCS library across every signer and verifier language.
3. Load public keys from a managed JWKS/KMS/HSM control plane with rotation and revocation evidence.
4. Add mTLS/OIDC authentication, tenant isolation, rate limits, structured audit logs, and secret redaction.
5. Implement a provider-specific connector contract covering authority, consistency, freshness, idempotency scope, regional behavior, webhook delay, and reversals.
6. Add failure fixtures for timeout-before-commit, timeout-after-commit, duplicate retry, stale read, concurrent refund, refund/chargeback collision, delayed failure, and reversal.
7. Keep raw payment payloads and PII in customer-controlled storage and export only minimized evidence.
8. Begin with read-only/shadow reconciliation and report incomplete visibility; make the protected path mandatory only after a design-partner pilot proves the need.
9. Have security, payments operations, internal audit, and dispute teams review the evidence boundary.

## Research and product documents

- [`docs/technical-architecture.md`](docs/technical-architecture.md)
- [`docs/deep-market-product-audit.md`](docs/deep-market-product-audit.md)
- [`docs/expert-recommendations-build-assessment.md`](docs/expert-recommendations-build-assessment.md)
- [`docs/pdf-strategy-review.md`](docs/pdf-strategy-review.md)
- [`docs/read-only-30-day-outreach.md`](docs/read-only-30-day-outreach.md)
- [`docs/read-only-reconciliation-code-review.md`](docs/read-only-reconciliation-code-review.md)
- [`schemas/reconciliation-event.schema.json`](schemas/reconciliation-event.schema.json)
- [`docs/90-day-go-to-market.md`](docs/90-day-go-to-market.md)

## License

MIT. See [`LICENSE`](LICENSE).

## Additional release documents

- [`docs/cryptographic-reconciliation-whitepaper.md`](docs/cryptographic-reconciliation-whitepaper.md)
- [`docs/investor-speaker-script-and-pitching-guidelines.md`](docs/investor-speaker-script-and-pitching-guidelines.md)
