# Review of StateProof Fact Check & Strategy PDF

## Decision

The PDF contains one important strategic improvement: StateProof should begin with a **read-only Refund Outcome Reconciler** rather than asking a new customer to make StateProof the mandatory financial execution path on day one.

That change lowers adoption friction and lets the product prove real leakage before it blocks or mediates live refunds. It should be treated as a **validation and wedge phase**, not as the final category.

The strongest sequence is:

> **Observe → reconcile → quantify leakage → prove evidence value → enforce selectively.**

StateProof should not become a generic monitoring dashboard. The read-only product must focus on transaction exceptions that ordinary traces and provider logs do not resolve cleanly.

## New claims confirmed by the PDF's sources

The PDF correctly adds competitors that must be reflected in the strategy.

**Salus is direct pre-action competition.** Y Combinator describes Salus as an API that validates agent actions at runtime, blocks incorrect actions, provides structured feedback for retries, and includes policy, evidence, idempotency, human escalation, and receipts. Salus's own site positions it as runtime authorization that checks policy, evidence, and intent before provider execution. This means StateProof cannot claim a new general-purpose pre-action guardrail or agent action receipt category. It reinforces the decision to differentiate on post-execution reconciliation and cross-system financial state.

**Razorpay Agent Studio shows that payment platforms are absorbing control and evidence features.** Its published terms classify refunds and other financial actions as transactional actions, provide configurable approval gates, retain financial-action audit trails for at least ten years under the stated terms, and describe append-only audit trails with cryptographic timestamping. This is strong evidence that approval, audit, and evidence are not safe standalone differentiators when a payment platform owns the workflow.

**Shopify's refund idempotency claim is confirmed.** Shopify's current `refundCreate` documentation says idempotency was optional from API version 2026-01 and required from 2026-04. Shopify therefore reduces the novelty of generic refund retry protection inside its own system. The remaining opportunity must be cross-system outcome reconciliation and competing-writer detection.

**AWS AgentCore Policy confirms the pre-action market is mature.** AWS documents gateway interception, deterministic policy enforcement, identity and input-parameter controls, temporal/session-aware rules, and audit logging. StateProof should integrate with AgentCore/OPA/Cedar rather than compete with those functions.

**Fini is evidence of adjacent refund/dispute automation, but its strongest commercial claims need qualification.** The reviewed Fini guide is vendor-authored marketing content. It supports the existence of policy-driven refund/dispute automation, audit trails, helpdesk/payment integrations, and evidence packaging as a competitive direction. Claims such as accuracy, query volume, certification portfolio, price, and deployment duration should not be used as independently verified market facts without direct primary documentation.

## What the PDF gets right

The PDF's central distinction is correct:

- Existing competitors focus heavily on whether a refund should happen and whether an agent may initiate it.
- The less-covered problem is what happened to the money across the payment provider, commerce system, helpdesk, agent, dispute process, and internal records.

The proposed read-only entry point is commercially sensible because it removes the most difficult initial objection: asking a new vendor to sit in front of live financial writes. It lets a customer compare StateProof's findings with existing records before trusting it to block or mediate actions.

The proposed exception types are well chosen:

- unknown outcomes after timeouts;
- delayed provider failures and reversals;
- refund-versus-dispute collisions;
- duplicate or excessive refunds across writers;
- mismatches between provider, order, helpdesk, and agent records.

The proposed evidence pack is also more commercially useful than a signed receipt alone. Operations, disputes, finance, and audit teams need a case-level explanation with events, state observations, policy version, amounts, timestamps, identifiers, and unresolved assumptions.

## What must be corrected or qualified

### Read-only mode is not automatically a moat

A watcher that reads APIs, webhooks, and logs can become a crowded observability or reconciliation product. It will be defensible only if it resolves a difficult, expensive class of exceptions that customers cannot reliably close with provider dashboards, internal scripts, SIEM, workflow history, or existing reconciliation tooling.

The read-only product must therefore output an operational decision, not merely a dashboard event:

- verified and matched;
- duplicate or excessive refund risk;
- refund/dispute collision;
- delayed failure or reversal;
- provider state unknown;
- cross-system mismatch;
- evidence incomplete;
- operator action required.

### The evidence pack must not overclaim

A StateProof evidence pack should clearly identify which facts came from the provider, commerce system, helpdesk, agent trace, or customer-owned record. A customer-signed receipt is not independent corroboration by itself. The pack should show source authority, timestamps, freshness, consistency assumptions, missing evidence, and contradictions.

### Read-only does not remove integration risk

The customer still must grant access to relevant sources. The product needs read access to the authoritative payment/refund record and enough commerce/helpdesk context to detect competing actions. If the product cannot identify a source of truth, it must return `INDETERMINATE` rather than infer a financial outcome.

### The three-month conversion target is a plan, not evidence

The PDF's 90-day plan is useful for execution, but it does not prove that customers will pay in three months. Paid conversion remains conditional on real exception volume, quantified avoided loss or labor, security acceptance, and a buyer willing to sponsor the next step.

### Do not use unsupported vendor metrics

Vendor-authored Fini numbers, Salus benchmark numbers, and any pricing or certification claim should be cited as vendor-reported unless independently verified. They are useful competitive signals, not market baselines.

## Revised product shape

### Phase 0: Refund Leakage Report

A read-only ingestion and analysis mode that accepts customer-approved exports, provider APIs, webhooks, and selected agent/helpdesk events. It produces a bounded report for a defined period, such as 60–90 days.

The report should quantify:

- duplicate or excessive refunds;
- refunds later failed or reversed;
- timeouts with no confirmed final state;
- refund-versus-dispute collisions;
- cross-system amount or status mismatches;
- manual investigation cases;
- evidence-preparation time;
- cases where the available data is insufficient to conclude.

This phase should be as low-permission as possible. It should not execute refunds.

### Phase 1: Shadow reconciliation

StateProof continuously watches a selected workflow but does not block writes. It produces alerts and case files, and compares its conclusion against the customer's authoritative records and operator decisions.

Success metrics should include precision, recall, false alarms, missed conflicts, time to resolution, and operator minutes saved.

### Phase 2: Selective enforcement

Only after the read-only and shadow phases demonstrate value should StateProof mediate a narrow cohort of high-risk refunds. The gate should be an upsell or controlled rollout, not a prerequisite for the first evaluation.

### Phase 3: Evidence and operations product

The commercial control plane can then provide:

- managed reconciliation;
- durable operation state;
- exception queue and escalation;
- bypass/coverage detection;
- connector conformance reporting;
- customer-controlled evidence retention;
- exports to support, finance, disputes, SIEM, and GRC.

## Revised first-customer profile

The PDF's target is directionally right: mid-market merchants with meaningful refund volume and multiple action sources.

The best first customer is not simply a merchant with many refunds. It is a merchant that has at least two of the following:

- several thousand refunds per month;
- Stripe plus Shopify or another commerce system;
- support automation or AI actions;
- multiple human and automated refund writers;
- known refund/dispute or reversal exceptions;
- a finance or support-operations team doing manual reconciliation;
- a technical owner willing to provide read-only access;
- a budget owner willing to pay for a measured pilot.

A customer with a single provider, one refund writer, low volume, and no exception queue is unlikely to feel enough pain.

## Revised 90-day plan

**Weeks 1–2:** interview payments, support operations, finance, disputes, and platform engineering. Obtain anonymized exception examples and agree on source access and metrics.

**Weeks 2–4:** produce a free or tightly limited Refund Leakage Report using read-only data. Do not promise prevention or compliance.

**Weeks 4–7:** run shadow reconciliation with alerts and weekly case reports. Compare StateProof conclusions to operator outcomes.

**Weeks 6–10:** convert the strongest workflow to a paid pilot. The price should be based on measured exception volume, investigation labor, and risk exposure, not on generic trace volume. Any numerical price range remains a hypothesis until buyers respond.

**Weeks 8–12:** offer selective enforcement for the highest-risk cohort only if the connector and evidence results pass security review. Agree in advance whether the outcome is production deployment, a defined extension, or stop.

## Final recommendation

Adopt the PDF's read-only-first entry point. Do not abandon the StateProof control-plane thesis; postpone enforcement until it is earned.

The public product should be described as:

> **StateProof is a refund outcome reconciliation and transaction-integrity reference implementation. It detects ambiguous, conflicting, delayed, or unsupported refund outcomes across payment, commerce, support, and agent systems, then produces bounded evidence for investigation. Enforcement is an optional later phase for workflows that prove the need.**

This entry point is stronger than leading with a mandatory gate because it is easier to evaluate, less disruptive, and more likely to reveal whether the problem is economically meaningful. The long-term differentiator remains connector correctness, cross-system exception resolution, trusted evidence, and eventual mandatory adoption—not signed receipts alone.

## Sources checked for the new claims

- [Salus on Y Combinator](https://www.ycombinator.com/companies/salus)
- [Salus official product site](https://usesalus.ai/)
- [Razorpay Agent Studio terms](https://razorpay.com/tnc/agent-studio/)
- [Shopify `refundCreate` documentation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/refundcreate)
- [AWS Bedrock AgentCore Policy documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
- [Fini refund/dispute operations guide](https://www.usefini.com/guides/ai-platforms-refund-dispute-operations)
