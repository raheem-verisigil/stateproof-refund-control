# StateProof Refund Control: Technical Architecture and Receipt Contract

## 1. Product boundary

StateProof Refund Control is a customer-VPC or customer-controlled service that mediates one refund/payment-adjustment workflow and verifies a bounded claim:

> For a supported connector, the requested refund was authorized under a named policy version, bound to a defined pre-state, submitted with a retry/concurrency control, and the authoritative payment/refund system reported the declared postcondition—or the result remains explicitly unknown, conflicted, or failed.

It does **not** prove model reasoning, legal compliance, absence of hidden side effects, or the correctness of the customer’s policy.

## 2. Trust boundaries

```text
+--------------------+       +----------------------------+
| Agent / support UI | ----> | StateProof Request Gateway  |
+--------------------+       +-------------+--------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
          +--------v---------+                          +--------v---------+
          | Identity + policy |                          | Context resolver |
          | OIDC/mTLS, OPA/   |                          | order/payment/  |
          | Cedar, invariants |                          | delivery/policy |
          +--------+----------+                          +--------+---------+
                   |                                             |
                   +----------------------+----------------------+
                                          v
                              +-----------+-----------+
                              | Refund execution      |
                              | connector              |
                              | capability credential  |
                              +-----------+-----------+
                                          |
                         +----------------+----------------+
                         |                                 |
                +--------v---------+               +-------v--------+
                | Authoritative     |               | Evidence vault |
                | ledger/API        |               | customer-owned |
                | pre/post state    |               | raw evidence  |
                +------------------+               +-------+--------+
                                                           |
                                                   +-------v--------+
                                                   | Receipt signer |
                                                   | customer KMS  |
                                                   +-------+--------+
                                                           |
                                                   +-------v--------+
                                                   | Offline verifier|
                                                   +----------------+
```

### Trust assumptions

- The customer identifies the authoritative refund system and approves its connector.
- The connector reports its consistency, freshness, and coverage limits honestly; the receipt records those assumptions.
- Signing keys are customer-held or customer-approved and are protected by KMS/HSM policy.
- The gateway is the mandatory path for the protected workflow. If a tool can bypass it, the receipt is not evidence of complete mediation.
- Raw prompts, PII, payment data, and full provider payloads remain in the customer’s evidence vault unless separately authorized.

## 3. Components

### Request Gateway

Accepts a `RefundRequest`, validates tenant and agent identity, assigns a correlation ID and nonce, and rejects requests without an approved workflow, purpose, or capability.

### Context Resolver

Fetches only fields required for refund eligibility and amount. It enforces source authority, tenant scope, freshness bounds, field minimization, and conflict detection. It returns `INSUFFICIENT_CONTEXT` rather than guessing.

### Policy and Invariant Engine

Evaluates OPA/Rego or Cedar-compatible inputs. Invariants include tenant/order binding, maximum amount, currency, refund-window eligibility, approval threshold, no prior completed refund for the same basis, and required source freshness.

### Authoritative Connector

The only component allowed to call the refund provider. It implements:

- provider-specific idempotency;
- conditional/versioned execution where available;
- provider operation or transaction ID capture;
- pre-state and post-state reads;
- timeout/retry/reconciliation state machine;
- conflict and partial-failure classification;
- compensation workflow handoff without pretending compensation is proof of success.

### Evidence Vault

Append-only, encrypted customer storage for raw request, source responses, policy input/output, connector telemetry, provider acknowledgements, post-state reads, reconciliation attempts, and receipt versions. The vault supports retention, deletion, legal hold, and access audit.

### Receipt Signer and Verifier

The signer creates the canonical JSON payload, computes the digest, and signs with a customer-controlled key. The standalone verifier checks schema, canonicalization, signature, key status, nonce/replay, policy/invariant results, state commitments, freshness, and evidence references. It returns `VERIFIED`, `REJECTED`, or `INDETERMINATE` with reasons.

## 4. State machine

```text
RECEIVED
  -> AUTHORIZED
  -> REJECTED_BY_POLICY
AUTHORIZED
  -> PRE_STATE_CAPTURED
  -> INSUFFICIENT_CONTEXT
PRE_STATE_CAPTURED
  -> EXECUTION_SUBMITTED
  -> REJECTED_BY_POLICY
EXECUTION_SUBMITTED
  -> COMMITTED_PENDING_VERIFY
  -> PROVIDER_REJECTED
  -> UNKNOWN_OUTCOME
  -> COMPENSATION_REQUIRED
COMMITTED_PENDING_VERIFY
  -> EXECUTED_AND_VERIFIED
  -> EXECUTED_BUT_POSTCONDITION_FAILED
  -> CONFLICT_DETECTED
UNKNOWN_OUTCOME
  -> EXECUTED_AND_VERIFIED
  -> PROVIDER_REJECTED
  -> CONFLICT_DETECTED
  -> COMPENSATION_REQUIRED
  -> UNKNOWN_OUTCOME
```

Terminal statuses are not necessarily irreversible business outcomes. `UNKNOWN_OUTCOME` remains open until reconciliation reaches a supported terminal state or is escalated to an operator.

## 5. Reconciliation loop

1. **Create attempt:** generate `receipt_id`, `correlation_id`, nonce, idempotency key, and canonical request digest.
2. **Authorize:** evaluate identity, purpose, tenant, amount, currency, policy version, and invariants.
3. **Capture pre-state:** read the authoritative refund/payment record with version/ETag/transaction snapshot and freshness timestamp.
4. **Submit once:** call the provider with the idempotency key and capability-scoped credential. Persist the outbound request before transmission.
5. **Classify response:** map provider response to `COMMITTED`, `REJECTED`, `TIMEOUT`, `CONFLICT`, or `UNKNOWN` without relying solely on HTTP status.
6. **Verify post-state:** read the authoritative system and evaluate the declared postcondition: refund status, amount, currency, target order/payment, and provider operation identity.
7. **Retry safely:** retry only through the same idempotency key or provider-supported reconciliation query. Never create a new refund attempt merely because the first request timed out.
8. **Handle conflict:** if another writer changed the order/payment/refund state, issue `CONFLICT_DETECTED`; do not overwrite or infer success.
9. **Compensate:** if partial execution occurred, create a separate human-approved compensation task. A compensation receipt must reference the original receipt and state what was and was not repaired.
10. **Finalize receipt:** sign each material state transition or issue a superseding receipt linked to the prior version. The verifier must detect replay and supersession.
11. **Export minimally:** send OTel/SIEM/GRC links and minimized receipt metadata; keep raw payment and PII evidence local.

### Reconciliation invariants

- Same logical refund request maps to one stable idempotency key.
- A timeout never maps directly to `FAILED` or `SUCCESS`.
- A second submission requires provider-confirmed absence of the first operation or an approved new business intent.
- Post-state must match target, amount, currency, and expected status.
- Receipt status cannot be stronger than its weakest evidence assumption.
- A compromised or revoked signer key makes verification `REJECTED` or `INDETERMINATE`, never silently valid.

## 6. JSON Schema

The following Draft 2020-12 schema defines the signed receipt envelope. The exact canonicalization profile must be frozen before interoperability testing.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://stateproof.example/schemas/refund-receipt-1.0.json",
  "title": "StateProof Refund Receipt",
  "type": "object",
  "additionalProperties": false,
  "required": ["receipt_version","receipt_id","issued_at","tenant","workflow","request","authorization","pre_state","execution","post_state","outcome","evidence","signature"],
  "properties": {
    "receipt_version": {"const": "1.0"},
    "receipt_id": {"type":"string","pattern":"^spr_[A-Za-z0-9_-]{16,}$"},
    "supersedes_receipt_id": {"type":"string"},
    "issued_at": {"type":"string","format":"date-time"},
    "expires_at": {"type":"string","format":"date-time"},
    "tenant": {
      "type":"object","additionalProperties":false,"required":["tenant_id","jurisdiction"],
      "properties":{"tenant_id":{"type":"string"},"jurisdiction":{"type":"string","pattern":"^[A-Z]{2}(-[A-Z0-9]+)?$"},"region":{"type":"string"}}
    },
    "workflow": {
      "type":"object","additionalProperties":false,"required":["workflow_id","workflow_version","connector_id","connector_version"],
      "properties":{"workflow_id":{"type":"string"},"workflow_version":{"type":"string"},"connector_id":{"type":"string"},"connector_version":{"type":"string"},"source_authority":{"type":"string"}}
    },
    "request": {
      "type":"object","additionalProperties":false,"required":["correlation_id","nonce","actor","agent","action_type","canonical_action_digest","idempotency_key"],
      "properties":{
        "correlation_id":{"type":"string"},"nonce":{"type":"string"},
        "actor":{"$ref":"#/$defs/subject"},"agent":{"$ref":"#/$defs/subject"},"model":{"$ref":"#/$defs/model"},
        "action_type":{"const":"refund"},"canonical_action_digest":{"$ref":"#/$defs/digest"},
        "idempotency_key":{"type":"string","minLength":16},"purpose":{"type":"string"},
        "target":{"type":"object","additionalProperties":false,"required":["order_id","payment_id","currency","amount_minor"],"properties":{"order_id":{"type":"string"},"payment_id":{"type":"string"},"currency":{"type":"string","pattern":"^[A-Z]{3}$"},"amount_minor":{"type":"integer","minimum":1}}}
      }
    },
    "authorization": {
      "type":"object","additionalProperties":false,"required":["policy_id","policy_version","decision","invariant_results"],
      "properties":{"policy_id":{"type":"string"},"policy_version":{"type":"string"},"decision":{"enum":["ALLOW","DENY","INDETERMINATE"]},"invariant_results":{"type":"array","items":{"$ref":"#/$defs/invariant"}},"approval":{"type":"object","additionalProperties":false,"properties":{"required":{"type":"boolean"},"approver_id":{"type":"string"},"approved_at":{"type":"string","format":"date-time"}}}}
    },
    "pre_state": {"$ref":"#/$defs/state_snapshot"},
    "execution": {
      "type":"object","additionalProperties":false,"required":["submitted_at","provider","attempts"],
      "properties":{"submitted_at":{"type":"string","format":"date-time"},"provider":{"type":"string"},"provider_operation_id":{"type":"string"},"provider_response_class":{"enum":["ACCEPTED","COMMITTED","REJECTED","TIMEOUT","CONFLICT","UNKNOWN"]},"attempts":{"type":"array","items":{"$ref":"#/$defs/attempt"}},"capability_id":{"type":"string"}}
    },
    "post_state": {"$ref":"#/$defs/state_snapshot"},
    "outcome": {
      "type":"object","additionalProperties":false,"required":["status","postcondition_result","reconciliation_state"],
      "properties":{"status":{"enum":["ALLOWED_NOT_EXECUTED","REJECTED_BY_POLICY","EXECUTED_AND_VERIFIED","EXECUTED_BUT_POSTCONDITION_FAILED","CONFLICT_DETECTED","COMPENSATION_REQUIRED","UNKNOWN_OUTCOME"]},"postcondition_result":{"enum":["PASS","FAIL","UNKNOWN"]},"reconciliation_state":{"enum":["NOT_REQUIRED","OPEN","RESOLVED","ESCALATED"]},"reason_codes":{"type":"array","items":{"type":"string"}},"human_summary":{"type":"string"}}
    },
    "evidence": {
      "type":"object","additionalProperties":false,"required":["evidence_scope","pre_state_commitment","post_state_commitment","freshness","vault_reference"],
      "properties":{"evidence_scope":{"enum":["MINIMAL_METADATA","CUSTOMER_VAULT_LINK","FULL_CUSTOMER_LOCAL"]},"pre_state_commitment":{"$ref":"#/$defs/digest"},"post_state_commitment":{"$ref":"#/$defs/digest"},"freshness":{"type":"object","additionalProperties":false,"required":["pre_state_age_ms","post_state_age_ms","max_allowed_age_ms"],"properties":{"pre_state_age_ms":{"type":"integer","minimum":0},"post_state_age_ms":{"type":"integer","minimum":0},"max_allowed_age_ms":{"type":"integer","minimum":0},"consistency_level":{"type":"string"}}},"vault_reference":{"type":"string"},"exported_fields":{"type":"array","items":{"type":"string"}},"assumptions":{"type":"array","items":{"type":"string"}}}
    },
    "signature": {
      "type":"object","additionalProperties":false,"required":["algorithm","key_id","canonicalization","signed_digest","value"],
      "properties":{"algorithm":{"const":"Ed25519"},"key_id":{"type":"string"},"canonicalization":{"const":"JCS-RFC8785"},"signed_digest":{"$ref":"#/$defs/digest"},"value":{"type":"string"},"key_status_at_signing":{"enum":["ACTIVE","UNKNOWN"]}}
    }
  },
  "$defs": {
    "digest":{"type":"string","pattern":"^sha256:[a-f0-9]{64}$"},
    "subject":{"type":"object","additionalProperties":false,"required":["subject_id","subject_type"],"properties":{"subject_id":{"type":"string"},"subject_type":{"enum":["HUMAN","SERVICE","AGENT"]},"issuer":{"type":"string"},"authn_context":{"type":"string"}}},
    "model":{"type":"object","additionalProperties":false,"required":["provider","model_id"],"properties":{"provider":{"type":"string"},"model_id":{"type":"string"},"version":{"type":"string"}}},
    "invariant":{"type":"object","additionalProperties":false,"required":["invariant_id","version","result"],"properties":{"invariant_id":{"type":"string"},"version":{"type":"string"},"result":{"enum":["PASS","FAIL","UNKNOWN"]},"evidence_ref":{"type":"string"}}},
    "state_snapshot":{"type":"object","additionalProperties":false,"required":["captured_at","source","commitment","version","read_consistency"],"properties":{"captured_at":{"type":"string","format":"date-time"},"source":{"type":"string"},"commitment":{"$ref":"#/$defs/digest"},"version":{"type":"string"},"read_consistency":{"type":"string"},"refund_status":{"type":"string"},"refunded_amount_minor":{"type":"integer","minimum":0},"currency":{"type":"string","pattern":"^[A-Z]{3}$"},"provider_operation_id":{"type":"string"}}},
    "attempt":{"type":"object","additionalProperties":false,"required":["attempt_no","sent_at","result"],"properties":{"attempt_no":{"type":"integer","minimum":1},"sent_at":{"type":"string","format":"date-time"},"result":{"enum":["ACK","COMMITTED","REJECTED","TIMEOUT","CONFLICT","UNKNOWN"]},"response_digest":{"$ref":"#/$defs/digest"},"error_code":{"type":"string"}}}
  }
}
```

## 7. Verification result contract

The verifier should return a separate result object:

```json
{
  "receipt_id": "spr_01J...",
  "verification": "VERIFIED",
  "checks": {
    "schema": "PASS",
    "signature": "PASS",
    "key_status": "PASS",
    "canonicalization": "PASS",
    "nonce_replay": "PASS",
    "policy_reference": "PASS",
    "pre_state": "PASS",
    "execution_binding": "PASS",
    "post_state": "PASS",
    "freshness": "PASS",
    "evidence_scope": "PASS"
  },
  "limitations": ["Verification covers the declared provider state and connector assumptions only."],
  "verified_at": "2026-09-27T00:00:00Z"
}
```

`INDETERMINATE` is required when the receipt is structurally valid but key status, freshness, source authority, or evidence coverage cannot be established. `REJECTED` is required for altered signatures, schema violations, replay, superseded receipts, or failed postcondition claims presented as verified.

## 8. MVP implementation sequence

1. Freeze schema and canonicalization tests.
2. Build a fake provider with injected timeouts, delayed visibility, duplicate requests, conflicts, and partial commits.
3. Implement connector state machine and property tests.
4. Build standalone verifier before dashboard.
5. Add customer-key signing and local evidence vault.
6. Add OPA/Cedar input adapter and deterministic tool interception.
7. Add OTel export and a minimal audit/reconciliation view.
8. Run a production-like pilot only after every adversarial fixture yields the expected status.
