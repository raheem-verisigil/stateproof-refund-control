# StateProof: Cryptographically Verifiable Reconciliation Engine

## Abstract

StateProof is a customer-controlled reconciliation engine for consequential refund and payment-adjustment workflows. Its purpose is not to certify an AI model or replace a payment processor. Its purpose is to preserve source facts, bind a logical transaction operation to its evidence, reconcile ambiguous outcomes across systems, and produce a signed receipt that an independent verifier can check.

The system is designed around a practical asymmetry: authorization and execution can be observed in one system, while the final financial outcome may emerge later across payment, commerce, support, dispute, and accounting systems. A successful API response is therefore not sufficient evidence of a successful business outcome.

## 1. Problem and scope

A refund request can time out after the provider accepted it, return success before downstream visibility is consistent, be retried by a second writer, fail later, reverse, or collide with a dispute. Existing policy engines, gateways, workflow systems, traces, and provider dashboards each cover part of this path. They do not necessarily produce a single, source-aware explanation of what happened across systems.

StateProof begins read-only. It ingests provider webhooks, API snapshots, imports, support/agent events, and dispute records. It groups facts by a stable logical operation and classifies the outcome only to the strength supported by the evidence. Selective enforcement is a later phase.

## 2. Threat and failure model

The engine is designed for accidental ambiguity, inconsistent state, duplicate writers, delayed provider visibility, replay, tampering, stale evidence, revoked keys, and incomplete source coverage. It does not assume that a provider is malicious or that cryptography can make a provider's statement true.

The engine does not prove model reasoning, policy wisdom, legal compliance, absence of hidden side effects, or completeness when a workflow bypasses the observed sources. Every receipt must carry authority, freshness, consistency, and coverage assumptions.

## 3. Architecture

The read-only path has five logical stages:

1. **Ingestion.** Accept webhooks, API snapshots, imports, and selected agent/support events.
2. **Normalization.** Preserve the raw evidence in customer-controlled storage and emit a normalized event with a payload digest.
3. **Operation grouping.** Link events using an operation ID and provider/order/payment identifiers without overwriting source facts.
4. **Reconciliation.** Compare amount, currency, target, status, provider operation identity, timestamps, and dispute/reversal context.
5. **Evidence packaging.** Produce a case file with source references, authority, observations, freshness, classifications, contradictions, assumptions, and next action.

The future enforcement path adds identity, policy, pre-state capture, idempotent execution, post-state verification, and receipt signing. The connector is the only component permitted to call a financial provider.

## 4. Cryptographic evidence model

Each material receipt contains a canonical unsigned payload and a signature envelope. The payload includes tenant and workflow identity, logical request identity, policy references, pre-state, execution attempts, post-state, outcome, evidence commitments, and signer metadata.

The signer computes a SHA-256 digest over the canonical payload and signs the canonical bytes with Ed25519. The signature envelope identifies the algorithm, key ID, canonicalization profile, digest, and signature value. Public keys are resolved from a customer-controlled or customer-approved key registry in production.

Cryptography provides integrity and signer authenticity for the receipt bytes. It does not provide independent truth about the provider. If a connector reports an incorrect state and signs it, the signature proves who signed the claim and whether it was altered afterward; it does not make the underlying claim correct. This limitation is central to honest verification.

The current reference implementation uses deterministic sorted-key JSON and documents the requirement to replace it with a standards-compliant RFC 8785/JCS implementation before cross-language interoperability. The canonicalization profile must be frozen and tested by multiple implementations before production use.

## 5. Verification contract

The independent verifier returns one of three results:

- `VERIFIED`: schema, digest, signature, key status, freshness, outcome logic, execution binding, and replay checks pass.
- `REJECTED`: a required check fails, including altered bytes, invalid signature, expired receipt, invalid outcome claim, duplicate receipt, or schema violation.
- `INDETERMINATE`: the structure is valid but authority, key status, freshness, or evidence coverage cannot be established.

Replay protection is claimed only after signature, digest, schema, freshness, outcome, and execution-binding checks complete. This prevents an invalid receipt from poisoning the replay store.

## 6. Safe reconciliation loop

A financial mutation must use one stable logical operation and idempotency key. After an ambiguous provider response such as timeout or unknown, the engine must query the provider using the original operation before attempting another submission. A provider may commit after the client stops waiting.

If lookup confirms the operation, the engine reads post-state and compares the target, payment, amount, currency, refund status, and provider operation ID. If the post-state mismatches, it returns an escalated or conflicted result rather than inferring success. If lookup confirms absence and policy allows another attempt, a later submission may use the same idempotency semantics or a separately approved business intent. A new refund must never be created solely because the first response timed out.

## 7. Read-only event contract

The `reconciliation-event-1.0` schema separates `event_id` from `operation_id`, `observed_at` from `received_at`, and source authority from classification. A normalized event includes source system, source record, connector version, provider status, target identifiers, actor, idempotency key when available, payload digest, evidence location, freshness, and consistency.

Classification is deliberately operational: `MATCHED`, `DUPLICATE_RISK`, `EXCESSIVE_REFUND_RISK`, `UNKNOWN_OUTCOME`, `DELAYED_FAILURE`, `REVERSED`, `REFUND_DISPUTE_CONFLICT`, `CROSS_SYSTEM_MISMATCH`, `INSUFFICIENT_EVIDENCE`, or `OPERATOR_REVIEW`.

The event is a fact record first and a conclusion second. Classifications must retain reason codes and next action. Evidence that cannot establish source authority or freshness must lower the claim to unknown or insufficient evidence.

## 8. Evidence retention and privacy

Raw provider payloads, prompts, payment data, and PII remain in customer-controlled storage unless separately authorized. StateProof exports minimized metadata, digests, source references, and case-level conclusions. Evidence storage must support encryption, retention, deletion, legal hold, access audit, and customer-controlled key policy.

A production deployment requires durable replay and operation storage, managed key rotation and revocation, mTLS/OIDC, tenant isolation, rate limits, structured audit logs, connector coverage reporting, and incident procedures.

## 9. Adversarial test matrix

A credible connector must pass fixtures for timeout-before-commit, timeout-after-commit, duplicate retry, stale read, concurrent refund, delayed failure, reversal, refund/dispute collision, partial commit, webhook duplication, out-of-order events, altered receipt, expired receipt, replay, revoked key, unavailable key, and missing evidence.

Tests must verify both positive and negative cases, including that an invalid receipt cannot reserve a replay identifier and that an ambiguous response never directly becomes success.

## 10. Product and commercial boundary

StateProof should not compete with general agent guardrails, policy engines, payment processors, observability suites, or workflow engines. Its wedge is cross-system outcome reconciliation for a high-loss transaction type. The buyer is a payments, support operations, finance-controls, disputes, or platform owner who already pays for manual investigation, leakage, or evidence preparation.

The adoption sequence is Observe → Reconcile → Quantify → Enforce. A read-only report establishes whether the exception volume is economically meaningful. Shadow reconciliation measures precision, coverage, investigation time, and evidence value. Selective enforcement is offered only after the customer trusts the connector and agrees on the control boundary.

## 11. Limitations and open research

The reference implementation is provider-neutral and does not include a production Stripe or Adyen connector. It does not prove that the selected source is authoritative, and its in-memory replay store is not suitable for multi-instance production. Its deterministic JSON profile is not yet a complete cross-language JCS implementation. These are explicit release limitations, not hidden assumptions.

The next research milestones are a real connector, provider-specific failure fixtures, event deduplication and ordering, durable operation state, evidence-pack review with control owners, and a paid design-partner pilot.

## Conclusion

StateProof's cryptographic engine is best understood as an evidence-integrity and reconciliation mechanism. It turns uncertain distributed-system outcomes into bounded, independently checkable claims without pretending that signatures replace provider authority or operational judgment. The strongest product path is to prove this value read-only, quantify the business pain, and earn selective enforcement through evidence.
