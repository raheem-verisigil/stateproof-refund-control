"""StateProof Refund Control reference implementation.

This module is intentionally provider-neutral. Production deployments should add a
provider connector that implements the AuthoritativeConnector protocol and replace
the in-memory replay store with durable, transactional storage.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Mapping, MutableMapping, Optional, Protocol, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, ValidationError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return dt.astimezone(timezone.utc)


def canonical_json(value: Any) -> bytes:
    """Deterministic JSON for the schema's JSON-safe values.

    This is a strict, UTF-8, sorted-key canonical form. For cross-language
    interoperability, pin an RFC 8785/JCS library in the production build and
    use the same canonicalizer in signer and verifier.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class ReceiptStatus(str, Enum):
    ALLOWED_NOT_EXECUTED = "ALLOWED_NOT_EXECUTED"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    EXECUTED_AND_VERIFIED = "EXECUTED_AND_VERIFIED"
    EXECUTED_BUT_POSTCONDITION_FAILED = "EXECUTED_BUT_POSTCONDITION_FAILED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    COMPENSATION_REQUIRED = "COMPENSATION_REQUIRED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"


class Verification(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    INDETERMINATE = "INDETERMINATE"


class ReceiptModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receipt_version: str = Field(pattern=r"^1\.0$")
    receipt_id: str = Field(pattern=r"^spr_[A-Za-z0-9_-]{16,}$")
    issued_at: datetime
    expires_at: Optional[datetime] = None
    tenant: Dict[str, Any]
    workflow: Dict[str, Any]
    request: Dict[str, Any]
    authorization: Dict[str, Any]
    pre_state: Dict[str, Any]
    execution: Dict[str, Any]
    post_state: Dict[str, Any]
    outcome: Dict[str, Any]
    evidence: Dict[str, Any]
    signature: Dict[str, Any]

    def unsigned_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(mode="json", exclude={"signature"})
        return payload

    def unsigned_bytes(self) -> bytes:
        return canonical_json(self.unsigned_payload())


@dataclass
class ReplayStore:
    """Replace with Redis/SQL conditional insert in production."""
    seen: MutableMapping[str, datetime] = field(default_factory=dict)

    def claim(self, receipt_id: str, now: datetime) -> bool:
        if receipt_id in self.seen:
            return False
        self.seen[receipt_id] = now
        return True


@dataclass
class KeyRecord:
    public_key: Ed25519PublicKey
    status: str = "ACTIVE"


class ReceiptVerifier:
    def __init__(self, keys: Mapping[str, KeyRecord], replay_store: Optional[ReplayStore] = None, clock=utc_now):
        self.keys = dict(keys)
        self.replay_store = replay_store or ReplayStore()
        self.clock = clock

    def verify(self, raw: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            receipt = ReceiptModel.model_validate(raw)
        except ValidationError as exc:
            return {"verification": Verification.REJECTED.value, "checks": {"schema": "FAIL"}, "reasons": exc.errors()}

        now = self.clock().astimezone(timezone.utc)
        checks: Dict[str, str] = {"schema": "PASS"}
        reasons: list[str] = []

        issued = parse_time(receipt.issued_at)
        if issued > now:
            checks["issued_at"] = "FAIL"; reasons.append("receipt issued_at is in the future")
        else:
            checks["issued_at"] = "PASS"
        if receipt.expires_at and parse_time(receipt.expires_at) <= now:
            checks["expiry"] = "FAIL"; reasons.append("receipt is expired")
        else:
            checks["expiry"] = "PASS"

        key_id = receipt.signature.get("key_id")
        key = self.keys.get(key_id)
        if not key:
            checks["key_status"] = "UNKNOWN"; reasons.append("signing key is not available")
        elif key.status != "ACTIVE":
            checks["key_status"] = "FAIL"; reasons.append("signing key is not active")
        else:
            checks["key_status"] = "PASS"

        expected_digest = "sha256:" + hashlib.sha256(receipt.unsigned_bytes()).hexdigest()
        checks["signed_digest"] = "PASS" if receipt.signature.get("signed_digest") == expected_digest else "FAIL"
        if checks["signed_digest"] == "FAIL": reasons.append("signed_digest does not match canonical receipt body")

        if key and key.status == "ACTIVE":
            try:
                signature = b64decode(receipt.signature["value"])
                key.public_key.verify(signature, receipt.unsigned_bytes())
                checks["signature"] = "PASS"
            except (InvalidSignature, KeyError, ValueError):
                checks["signature"] = "FAIL"; reasons.append("Ed25519 signature verification failed")
        else:
            checks["signature"] = "UNKNOWN"

        checks["freshness"] = self._freshness(receipt, reasons)
        checks["outcome_logic"] = self._outcome_logic(receipt, reasons)
        checks["execution_binding"] = self._execution_binding(receipt, reasons)

        # Do not claim the replay key until the receipt is otherwise valid;
        # otherwise an attacker could poison the store with a bad signature.
        if any(v == "FAIL" for v in checks.values()):
            checks["replay"] = "NOT_EVALUATED"
        elif not self.replay_store.claim(receipt.receipt_id, now):
            checks["replay"] = "FAIL"; reasons.append("receipt_id has already been observed")
        else:
            checks["replay"] = "PASS"

        if any(v == "FAIL" for v in checks.values()):
            result = Verification.REJECTED
        elif any(v == "UNKNOWN" for v in checks.values()):
            result = Verification.INDETERMINATE
        else:
            result = Verification.VERIFIED
        return {"receipt_id": receipt.receipt_id, "verification": result.value, "checks": checks, "reasons": reasons, "verified_at": now.isoformat().replace("+00:00", "Z")}

    def _freshness(self, receipt: ReceiptModel, reasons: list[str]) -> str:
        freshness = receipt.evidence.get("freshness", {})
        required = ("pre_state_age_ms", "post_state_age_ms", "max_allowed_age_ms")
        if any(k not in freshness for k in required):
            reasons.append("freshness evidence is incomplete"); return "UNKNOWN"
        if max(freshness["pre_state_age_ms"], freshness["post_state_age_ms"]) > freshness["max_allowed_age_ms"]:
            reasons.append("state evidence exceeds freshness bound"); return "FAIL"
        return "PASS"

    def _outcome_logic(self, receipt: ReceiptModel, reasons: list[str]) -> str:
        status = receipt.outcome.get("status")
        post = receipt.outcome.get("postcondition_result")
        valid_statuses = {s.value for s in ReceiptStatus}
        if status not in valid_statuses:
            reasons.append("unknown outcome status"); return "FAIL"
        if status == ReceiptStatus.EXECUTED_AND_VERIFIED.value and post != "PASS":
            reasons.append("verified execution requires PASS postcondition"); return "FAIL"
        if status == ReceiptStatus.UNKNOWN_OUTCOME.value and post != "UNKNOWN":
            reasons.append("unknown outcome requires UNKNOWN postcondition"); return "FAIL"
        return "PASS"

    def _execution_binding(self, receipt: ReceiptModel, reasons: list[str]) -> str:
        request_key = receipt.request.get("idempotency_key")
        attempts = receipt.execution.get("attempts", [])
        if not request_key or not isinstance(attempts, list):
            reasons.append("missing idempotency key or execution attempts"); return "FAIL"
        if len({a.get("attempt_no") for a in attempts}) != len(attempts):
            reasons.append("duplicate attempt number"); return "FAIL"
        return "PASS"


class AuthoritativeConnector(Protocol):
    def lookup(self, idempotency_key: str) -> Mapping[str, Any]: ...
    def submit_refund(self, request: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...
    def read_post_state(self, target: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass
class ReconciliationLoop:
    connector: AuthoritativeConnector
    max_attempts: int = 3

    def reconcile(self, request: Mapping[str, Any], existing_receipt: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        key = request["idempotency_key"]
        status = self.connector.lookup(key)
        if self._apply_lookup(request, existing_receipt, status, "RECONCILED_BY_IDEMPOTENCY_KEY"):
            return existing_receipt

        for attempt_no in range(1, self.max_attempts + 1):
            response = self.connector.submit_refund(request, key)
            existing_receipt["execution"].setdefault("attempts", []).append({"attempt_no": attempt_no, "sent_at": utc_now().isoformat().replace("+00:00", "Z"), "result": response.get("result", "UNKNOWN"), "provider_operation_id": response.get("provider_operation_id")})
            if response.get("result") in {"TIMEOUT", "UNKNOWN"}:
                existing_receipt["outcome"] = {"status": ReceiptStatus.UNKNOWN_OUTCOME.value, "postcondition_result": "UNKNOWN", "reconciliation_state": "OPEN", "reason_codes": ["PROVIDER_RESPONSE_AMBIGUOUS"]}
                # Reconcile the original logical operation before any later
                # submission; a provider may commit after the timeout.
                status = self.connector.lookup(key)
                if self._apply_lookup(request, existing_receipt, status, "RECONCILED_AFTER_AMBIGUOUS_RESPONSE"):
                    return existing_receipt
                continue
            if response.get("result") in {"REJECTED", "CONFLICT"}:
                st = ReceiptStatus.PROVIDER_REJECTED.value if response.get("result") == "REJECTED" else ReceiptStatus.CONFLICT_DETECTED.value
                existing_receipt["outcome"] = {"status": st, "postcondition_result": "FAIL", "reconciliation_state": "RESOLVED", "reason_codes": ["PROVIDER_REJECTED_OR_CONFLICT"]}
                return existing_receipt
            post = self.connector.read_post_state(request["target"])
            if self._matches(request["target"], post, response):
                existing_receipt["outcome"] = {"status": ReceiptStatus.EXECUTED_AND_VERIFIED.value, "postcondition_result": "PASS", "reconciliation_state": "RESOLVED", "reason_codes": ["POST_STATE_MATCHED"]}
                existing_receipt["execution"]["provider_operation_id"] = response.get("provider_operation_id")
                return existing_receipt
            existing_receipt["outcome"] = {"status": ReceiptStatus.EXECUTED_BUT_POSTCONDITION_FAILED.value, "postcondition_result": "FAIL", "reconciliation_state": "ESCALATED", "reason_codes": ["POST_STATE_MISMATCH"]}
            return existing_receipt
        return existing_receipt

    def _apply_lookup(self, request: Mapping[str, Any], receipt: MutableMapping[str, Any], status: Mapping[str, Any], reason: str) -> bool:
        if not status.get("known"):
            return False
        operation_id = status.get("provider_operation_id")
        receipt["execution"]["provider_operation_id"] = operation_id
        post = self.connector.read_post_state(request["target"])
        if self._matches(request["target"], post, {"provider_operation_id": operation_id}):
            receipt["outcome"] = {"status": ReceiptStatus.EXECUTED_AND_VERIFIED.value, "postcondition_result": "PASS", "reconciliation_state": "RESOLVED", "reason_codes": [reason]}
        else:
            receipt["outcome"] = {"status": ReceiptStatus.EXECUTED_BUT_POSTCONDITION_FAILED.value, "postcondition_result": "FAIL", "reconciliation_state": "ESCALATED", "reason_codes": ["LOOKUP_POST_STATE_MISMATCH"]}
        return True

    @staticmethod
    def _matches(target: Mapping[str, Any], post: Mapping[str, Any], response: Mapping[str, Any]) -> bool:
        return (post.get("order_id") == target.get("order_id") and post.get("payment_id") == target.get("payment_id") and post.get("currency") == target.get("currency") and post.get("refunded_amount_minor") == target.get("amount_minor") and post.get("refund_status") == "succeeded" and (not response.get("provider_operation_id") or post.get("provider_operation_id") == response.get("provider_operation_id")))


def make_idempotency_key(prefix: str = "rf") -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"
