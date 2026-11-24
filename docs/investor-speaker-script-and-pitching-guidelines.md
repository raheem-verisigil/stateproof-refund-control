# StateProof investor speaker script and pitching guidelines

## Core pitch

StateProof reconciles what actually happened after automated refunds across payment, commerce, support, agent, and dispute systems. We start read-only, prove the exceptions and investigation cost, and earn the right to selectively enforce high-risk workflows.

## Slide-by-slide script

### 1. StateProof

StateProof is a refund outcome reconciliation engine for automated financial actions. We are not asking enterprises to trust a new gateway with live money on day one. We begin by observing the records they already own, reconciling the outcomes, and proving whether the gap is economically meaningful.

### 2. The failure happens after the tool call

An agent can say “refund submitted” after an HTTP success, a timeout, or a webhook. None of those alone proves that the right amount reached the right payment exactly once and stayed correct after later failures or disputes. That unresolved state becomes duplicate refunds, false success, and manual reconciliation work.

### 3. The pre-action layer is crowded

We are deliberately not another generic agent guardrail, policy engine, payment API, or trace viewer. Salus, AWS AgentCore, OPA/Cedar, payment providers, commerce platforms, and helpdesks increasingly cover those layers. Our question is different: what actually happened across the systems after the call?

### 4. Cross-system outcome truth

Provider state, order state, support action, and dispute state can disagree or arrive at different times. StateProof preserves each source fact, its authority, its observation time, and its evidence. It returns a bounded classification rather than pretending that one success field settles the case.

### 5. Read-only reconciler

Our first product is a Refund Outcome Reconciler. It ingests webhooks, snapshots, imports, and selected agent or support events; groups them by logical operation; flags unknown outcomes, duplicates, reversals, delayed failures, and collisions; and creates an evidence pack. The pilot does not execute refunds.

### 6. Source-aware event model

The event contract separates the source event from the logical operation and the later classification. It records authority, connector version, observed and received timestamps, freshness, consistency, payload digest, and evidence location. Facts come first; interpretation remains traceable.

### 7. Observe → Reconcile → Quantify → Enforce

The commercial sequence is intentional. Observe safely. Reconcile the records. Quantify confirmed exceptions, labor, and evidence gaps. Only then consider selective enforcement for a narrow high-risk cohort. This makes the first purchase a low-friction diagnostic rather than a bet on a new mandatory control path.

### 8. First buyer

The first buyer has meaningful refund volume, multiple writers, more than one relevant system, and visible manual exception work. The champion may be payments operations, support operations, finance controls, disputes, or platform engineering. The budget owner must agree that the measured problem is worth solving.

### 9. Proof plan

In the first two weeks we choose one workflow, source of truth, owner, baseline, and stop criteria. We then run a read-only leakage report and a shadow reconciliation pilot. We measure precision, coverage, missed cases, operator time, and evidence preparation. We continue only if the data proves value.

### 10. Ask

We are funding the evidence first: one connector, event ingestion, case-level evidence, and two design partners. We are not promising a universal certificate authority or a giant platform. If the pilot proves material leakage and customer pull, selective enforcement becomes the next product; if not, we stop or narrow the thesis.

## Pitching guidelines

### Lead with the painful incident class

Use timeout-after-commit, duplicate retry, delayed reversal, and refund/dispute collision as concrete examples. Avoid starting with cryptography, AI safety, or a broad “trust layer” slogan.

### Explain the wedge before the moat

Investors should understand why a customer will accept the first deployment: read-only access, one workflow, no refund execution, and an immediate exception report. Then explain the moat as accumulated connector semantics, failure fixtures, source authority models, evidence-pack workflow, and eventual control adoption.

### Be explicit about crowded categories

Say that pre-action guardrails, policy engines, payment APIs, workflows, and observability are crowded. The credibility comes from narrowing the claim and positioning StateProof as an adjacent reconciliation layer.

### Never overclaim cryptography

Say: “The signature proves the integrity and signer authenticity of the receipt.” Do not say: “The signature proves the refund happened.” The provider and source authority establish the underlying fact; cryptography makes the recorded claim tamper-evident.

### Avoid unsupported numbers

Do not invent market size, customer count, savings, accuracy, pricing, or conversion rates. Use pilot metrics as targets or hypotheses until measured. If asked about pricing, say the pilot will be priced against confirmed exception volume, investigation labor, and workflow value after discovery.

### Answer the hard investor questions directly

**Why won't Stripe, Shopify, AWS, or the helpdesk build this?** They may cover their own surface well. Our hypothesis is that customers still need cross-system reconciliation across providers and writers; the pilot must prove that gap exists and matters.

**Why is this not observability?** Observability reports traces and events. StateProof classifies transaction outcomes against authority, freshness, target, amount, status, and evidence assumptions and produces an operational case file.

**Why will customers share data?** Start with read-only exports or customer-controlled deployment, minimize fields, keep raw evidence local, and establish written access and deletion boundaries.

**What is the moat?** No single signed receipt. The moat is connector-specific semantics, difficult failure fixtures, source authority and evidence handling, case-resolution workflow, and the operational trust required for selective enforcement.

**What would kill the company?** Three consecutive leakage reports with immaterial exception value, no control owner willing to share read-only data, or native tools resolving the same cross-system cases with little labor.

## Delivery style

Use a calm technical tone. Pause after the problem and after the crowded-market slide. Use “we are testing” for hypotheses and “we implemented” only for current code. Keep the first run to approximately eight minutes, reserving two minutes for objections. End with the proof plan and decision rule, not with a claim of inevitability.
