import base64
import copy
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from verifier import KeyRecord, ReceiptModel, ReceiptVerifier, ReconciliationLoop, ReplayStore, canonical_json


def signed_receipt(private_key, **overrides):
    now = datetime.now(timezone.utc)
    receipt = {
        "receipt_version": "1.0",
        "receipt_id": "spr_test_receipt_0001",
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "tenant": {"tenant_id": "t1", "jurisdiction": "US"},
        "workflow": {"workflow_id": "refund", "workflow_version": "1", "connector_id": "fake", "connector_version": "1"},
        "request": {"correlation_id": "c1", "nonce": "n1", "actor": {"subject_id": "u1", "subject_type": "HUMAN"}, "agent": {"subject_id": "a1", "subject_type": "AGENT"}, "action_type": "refund", "canonical_action_digest": "sha256:" + "0" * 64, "idempotency_key": "rf_test_1234567890", "target": {"order_id": "o1", "payment_id": "p1", "currency": "USD", "amount_minor": 100}},
        "authorization": {"policy_id": "refund-policy", "policy_version": "1", "decision": "ALLOW", "invariant_results": []},
        "pre_state": {"captured_at": now.isoformat(), "source": "ledger", "commitment": "sha256:" + "1" * 64, "version": "v1", "read_consistency": "strong"},
        "execution": {"submitted_at": now.isoformat(), "provider": "fake", "attempts": [{"attempt_no": 1, "sent_at": now.isoformat(), "result": "COMMITTED"}]},
        "post_state": {"captured_at": now.isoformat(), "source": "ledger", "commitment": "sha256:" + "2" * 64, "version": "v2", "read_consistency": "strong"},
        "outcome": {"status": "EXECUTED_AND_VERIFIED", "postcondition_result": "PASS", "reconciliation_state": "RESOLVED"},
        "evidence": {"evidence_scope": "MINIMAL_METADATA", "pre_state_commitment": "sha256:" + "1" * 64, "post_state_commitment": "sha256:" + "2" * 64, "freshness": {"pre_state_age_ms": 100, "post_state_age_ms": 100, "max_allowed_age_ms": 5000}, "vault_reference": "vault://1"},
        "signature": {"algorithm": "Ed25519", "key_id": "key-1", "canonicalization": "JCS-RFC8785", "signed_digest": "", "value": "", "key_status_at_signing": "ACTIVE"},
    }
    receipt.update(overrides)
    body = ReceiptModel.model_validate(receipt).unsigned_bytes()
    import hashlib
    receipt["signature"]["signed_digest"] = "sha256:" + hashlib.sha256(body).hexdigest()
    receipt["signature"]["value"] = base64.urlsafe_b64encode(private_key.sign(body)).decode().rstrip("=")
    return receipt


def test_valid_receipt_verifies():
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    verifier = ReceiptVerifier({"key-1": KeyRecord(public)}, ReplayStore())
    result = verifier.verify(signed_receipt(private))
    assert result["verification"] == "VERIFIED"


def test_tampering_is_rejected():
    private = Ed25519PrivateKey.generate()
    verifier = ReceiptVerifier({"key-1": KeyRecord(private.public_key())}, ReplayStore())
    receipt = signed_receipt(private)
    receipt["request"]["target"]["amount_minor"] = 999
    assert verifier.verify(receipt)["verification"] == "REJECTED"


def test_invalid_receipt_does_not_poison_replay_store():
    private = Ed25519PrivateKey.generate()
    verifier = ReceiptVerifier({"key-1": KeyRecord(private.public_key())}, ReplayStore())
    invalid = signed_receipt(private)
    invalid["request"]["target"]["amount_minor"] = 999
    assert verifier.verify(invalid)["verification"] == "REJECTED"
    assert verifier.verify(signed_receipt(private))["verification"] == "VERIFIED"


def test_replay_is_rejected():
    private = Ed25519PrivateKey.generate()
    verifier = ReceiptVerifier({"key-1": KeyRecord(private.public_key())}, ReplayStore())
    receipt = signed_receipt(private)
    assert verifier.verify(receipt)["verification"] == "VERIFIED"
    assert verifier.verify(receipt)["verification"] == "REJECTED"


def test_expired_receipt_is_rejected():
    private = Ed25519PrivateKey.generate()
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    verifier = ReceiptVerifier({"key-1": KeyRecord(private.public_key())}, ReplayStore())
    receipt = signed_receipt(private, expires_at=past)
    assert verifier.verify(receipt)["verification"] == "REJECTED"


def test_unknown_outcome_requires_unknown_postcondition():
    private = Ed25519PrivateKey.generate()
    verifier = ReceiptVerifier({"key-1": KeyRecord(private.public_key())}, ReplayStore())
    receipt = signed_receipt(private, outcome={"status": "UNKNOWN_OUTCOME", "postcondition_result": "PASS", "reconciliation_state": "OPEN"})
    assert verifier.verify(receipt)["verification"] == "REJECTED"


class FakeConnector:
    def __init__(self):
        self.calls = 0
        self.lookups = 0

    def lookup(self, idempotency_key):
        self.lookups += 1
        if self.calls == 1 and self.lookups >= 2:
            return {"known": True, "provider_operation_id": "op-1"}
        return {"known": False}

    def submit_refund(self, request, idempotency_key):
        self.calls += 1
        return {"result": "TIMEOUT" if self.calls == 1 else "COMMITTED", "provider_operation_id": "op-1"}

    def read_post_state(self, target):
        return {**target, "refund_status": "succeeded", "refunded_amount_minor": target["amount_minor"], "provider_operation_id": "op-1"}


def test_timeout_reconciles_using_same_key():
    connector = FakeConnector()
    loop = ReconciliationLoop(connector, max_attempts=2)
    receipt = {"execution": {"attempts": []}, "outcome": {}}
    request = {"idempotency_key": "rf_test_1234567890", "target": {"order_id": "o1", "payment_id": "p1", "currency": "USD", "amount_minor": 100}}
    result = loop.reconcile(request, receipt)
    assert result["outcome"]["status"] == "EXECUTED_AND_VERIFIED"
    assert [a["result"] for a in result["execution"]["attempts"]] == ["TIMEOUT"]
    assert connector.lookups == 2


def test_timeout_before_commit_can_submit_after_lookup_confirms_absence():
    class BeforeCommitConnector(FakeConnector):
        def lookup(self, idempotency_key):
            self.lookups += 1
            return {"known": False}

    connector = BeforeCommitConnector()
    loop = ReconciliationLoop(connector, max_attempts=2)
    receipt = {"execution": {"attempts": []}, "outcome": {}}
    request = {"idempotency_key": "rf_test_1234567890", "target": {"order_id": "o1", "payment_id": "p1", "currency": "USD", "amount_minor": 100}}
    result = loop.reconcile(request, receipt)
    assert result["outcome"]["status"] == "EXECUTED_AND_VERIFIED"
    assert [a["result"] for a in result["execution"]["attempts"]] == ["TIMEOUT", "COMMITTED"]
    assert connector.lookups == 2
