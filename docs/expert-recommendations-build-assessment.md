# StateProof expert recommendations: build assessment

## Decision

The expert recommendations should be adopted in substance. They strengthen StateProof by moving the product from a signed-receipt prototype toward a narrow **transaction-integrity and exception-resolution control** for high-risk refunds.

They do not justify broadening the project into agent observability, a policy engine, a workflow engine, a payment processor, or a generic compliance platform.

The correct implementation strategy is:

1. Keep the public product narrow: support- or AI-initiated refunds.
2. Make the central object a durable protected transaction operation.
3. Make reconciliation and exception resolution the commercial value.
4. Keep receipts as evidence infrastructure, not the headline product.
5. Integrate with existing identity, policy, workflow, payment, observability, and GRC systems.
6. Add only the minimum code required to demonstrate one provider-specific end-to-end path.

## What the expert got right

The strongest recommendations are consistent with the independent market audit:

- The problem is distributed-systems and payment-operations pain, not an AI-only problem.
- The category is crowded at observability, policy, gateways, workflows, payment APIs, and cryptographic evidence.
- The residual gap is the post-action boundary: what happened after a consequential external mutation, especially after timeout, asynchronous acceptance, reversal, competing writers, or delayed failure.
- A receipt is an output. Exception resolution is recurring operational work and is more likely to justify a budget.
- The open-source layer should reduce integration friction, while production value should come from connector correctness, durable operations, managed reconciliation, evidence handling, support, and control-function acceptance.
- The first buyer should be a payments/support operations owner paired with a technical champion, not an undifferentiated AI-platform audience.
- A paid, time-boxed pilot with pre-agreed success criteria is better evidence than developer enthusiasm.
- The real moat is provider-specific semantics, failure fixtures, trusted evidence consumption, and mandatory workflow adoption.

## What is already implemented

The current repository already provides a useful reference base:

- Pydantic receipt validation with forbidden extra fields.
- Ed25519 signature verification.
- Deterministic signed-body hashing, with a documented warning that production must use a standards-compliant RFC 8785 implementation.
- Receipt expiry and future-issuance checks.
- Freshness-bound checks.
- Explicit verification outcomes: `VERIFIED`, `REJECTED`, and `INDETERMINATE`.
- Replay protection with a regression test showing invalid receipts cannot poison the replay store.
- Basic execution binding through idempotency key and unique attempt numbers.
- A provider-neutral connector protocol.
- A basic reconciliation loop and test for a timeout followed by a successful outcome.
- A read-only HTTP verifier suitable for a Railway demonstration.

These capabilities should be described as reference behavior, not production guarantees.

## Critical code-level gap found

The current `ReconciliationLoop` records a `TIMEOUT` or `UNKNOWN` response and then can call `submit_refund` again on the next loop iteration. It uses the same idempotency key, which is safer than generating a new key, but it does not first perform a provider lookup or reconciliation query after the ambiguous response.

The expert recommendation is stronger and should be implemented:

> After an ambiguous submission, query the provider using the original logical operation and idempotency key before attempting another submission.

The implementation should also preserve the distinction between:

- committed but not yet visible;
- rejected by provider;
- provider conflict or duplicate/in-progress response;
- postcondition mismatch;
- delayed failure or reversal;
- unresolved unknown outcome.

This is the highest-priority code correction before public release or live testing.

## Adopt before GitHub/Railway

### A. Correct reconciliation semantics

- Query by the original logical operation after timeout.
- Do not create a second attempt until the connector proves that the original operation was not committed and the business policy permits another attempt.
- Add explicit connector methods for `lookup`, `read_post_state`, and provider-event ingestion.
- Add tests for timeout-after-commit, timeout-before-commit, provider duplicate/in-progress, and delayed failure.

### B. Publish a connector contract

Document, per provider:

- authoritative source of truth;
- idempotency key scope and retention;
- read-after-write delay;
- webhook ordering and duplication assumptions;
- regional/account limitations;
- provider operation identifiers;
- refund, reversal, dispute, and partial-refund semantics;
- conditions under which post-state is strong enough for `VERIFIED`.

A connector that cannot describe these properties must return `INDETERMINATE` rather than imply certainty.

### C. Add a durable-operation model to the protocol

The receipt should be linked to a stable logical operation created before external execution. The public reference implementation can remain storage-neutral, but the contract should define:

- `operation_id`;
- operation status and version;
- stable business target;
- idempotency key;
- attempt history;
- superseding receipts;
- reconciliation checkpoints;
- last-known provider event and read timestamps.

### D. Add the exception-resolution boundary

Do not build a large dashboard yet. Add a small, provider-neutral exception object and deterministic resolver for:

- timeout beyond expected window;
- delayed failure;
- reversal;
- duplicate or excessive refund;
- refund-versus-chargeback conflict;
- stale or contradictory post-state;
- missing evidence.

Each exception should have a reason code, current evidence status, next permitted action, escalation state, and immutable history.

### E. Strengthen public honesty

Keep the README language adopted in the market audit. Clearly label:

- reference implementation;
- read-only Railway demo;
- no live refunds;
- no durable production replay store;
- no provider connector included yet;
- no legal/compliance/model-correctness guarantee;
- no claim that a customer-signed receipt independently proves provider truth.

## Defer until a design partner requires it

- Full observability dashboard.
- General-purpose policy engine.
- New identity provider.
- Universal payment-provider coverage.
- Autonomous compensation or automatic financial retries.
- Broad chargeback-resolution platform.
- Multi-industry provenance product.
- Enterprise compliance automation suite.
- Complex visual exception console.
- Pricing commitments based on unvalidated market rates.

The expert's illustrative pilot and annual price ranges are useful for conversations but are not evidence of willingness to pay. They should remain hypotheses.

## Recommended build sequence

### Release 0.1: public reference implementation

- Correct timeout reconciliation semantics.
- Add connector contract and failure fixtures.
- Add durable-operation and exception schemas.
- Keep Railway service read-only.
- Include tests and explicit limitations.

### Pilot 0.2: one real connector

- Stripe test-mode connector or simulator.
- One commerce/order context.
- Shadow mode before enforcement.
- Provider event deduplication and reconciliation.
- Baseline metrics from a design partner.

### Production candidate 0.3

- Durable operation store.
- Customer-controlled evidence vault.
- Managed key lifecycle.
- Bypass/coverage detection.
- Exception queue and escalation workflow.
- Security and control-function review.

### Expansion gate

Expand beyond refunds only if one customer pays for the first workflow and the pilot shows measurable reduction in exception labor, incorrect/duplicate refunds, unresolved outcomes, or evidence-preparation effort.

## Final build judgment

Adopt the expert's **transaction operation + reconciliation + exception resolution** model. Do not adopt its recommendations as permission to build a larger platform.

The next build target is not another receipt feature. It is a safer reconciliation loop, a documented connector contract, and a small exception object that helps an operator resolve ambiguous refunds. Those changes make the project more useful, more credible to design partners, and more defensible without moving it into a crowded category.
