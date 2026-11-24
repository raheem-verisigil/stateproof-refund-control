# StateProof Refund Control: 90-Day Go-to-Market Strategy

## Objective

Secure **two design partners and at least one paid 90-day pilot** for one refund/payment-adjustment workflow. The goal is not broad awareness. The goal is a buyer-approved proof that StateProof reduces a measurable operational loss or reconciliation cost versus the customer’s existing stack.

## Ideal customer profile

Prioritize organizations with all of the following:

- high refund, credit, chargeback, or payment-adjustment volume;
- AI support, finance, or operations automation already in production or pilot;
- a system of record with a stable API and some form of idempotency, operation ID, version, or conditional write;
- a recent incident, audit exception, duplicate-action problem, or manual reconciliation burden;
- a named owner for refunds/payments operations;
- security/compliance willingness to run a customer-VPC or local connector;
- an existing baseline using workflow orchestration, policy-as-code, observability, or manual reconciliation.

### Priority segments

1. **Fintechs and payment platforms:** strongest pain and clearest state semantics; often faster than tier-one banks.
2. **Marketplaces and commerce platforms:** high refund volume, order/payment/delivery data, support-agent use cases.
3. **Digital insurers:** valuable but more complex; use only if claim/refund boundaries are clear.
4. **B2B SaaS with billing operations:** easier access and lower regulatory complexity; good technical design partners.
5. **Large banks or global payment processors:** strategic lighthouse targets, but do not make them the only pipeline because procurement may exceed 90 days.

## Buying committee

- **Economic buyer:** Head/VP of Payments, Refunds, Customer Operations, or Risk Operations.
- **Technical champion:** VP Platform Engineering, AI Platform Lead, or Principal Engineer responsible for agent deployment.
- **Control approver:** Security Engineering, Compliance, Internal Audit, or Model Risk.
- **Workflow owner:** the person accountable for refund losses, manual reconciliation, or customer-impacting errors.

Never pitch only to an AI innovation lab. Innovation teams can sponsor experiments but may not own a production budget.

## Positioning

### One-sentence pitch

> StateProof prevents an AI refund agent from treating an ambiguous provider response as success: it binds authorization and policy to the intended refund, reconciles timeouts and retries against the authoritative ledger, and produces a customer-verifiable result.

### Discovery questions

1. How many refunds or adjustments are initiated through automation today?
2. What happens when the provider times out after accepting a request?
3. How do you distinguish rejected, committed, duplicated, and unknown refunds?
4. How many staff-hours per month are spent reconciling agent actions to the ledger?
5. Which system is authoritative for refund status and amount?
6. Does it expose idempotency keys, operation IDs, versions, ETags, or reconciliation queries?
7. Who owns the financial or customer-impacting loss when an automated refund is wrong?
8. What evidence must be assembled for an incident, audit, or customer dispute?
9. What existing systems would StateProof need to outperform or complement?
10. Would you pay for a 90-day pilot if the acceptance criteria were met?

### Disqualifiers

Exit quickly if:

- there is no high-consequence workflow or measurable loss;
- the customer has no authoritative state source;
- all actions are already protected by a mature native transaction and reconciliation system with no remaining gap;
- the customer requires raw data to leave a restricted environment;
- the action cannot be mediated through a mandatory gateway;
- the buyer will not define a baseline or commit an acceptance owner;
- procurement timing makes a 90-day paid decision impossible.

## Offer design

### Paid pilot package

**90 days, one workflow, one connector, one customer environment.** Include:

- customer-VPC connector;
- policy/invariant integration;
- refund request interception;
- authoritative pre/post-state reads;
- idempotency and timeout reconciliation;
- signed receipts using customer-approved keys;
- independent verifier;
- failure-injection test report;
- OTel/SIEM/GRC export;
- weekly operating review;
- final ROI and security report.

### Pilot pricing hypothesis

Propose **$35,000–$60,000** for the first pilot, with an explicit conversion option to **$75,000–$150,000 annual pricing** for one protected workflow. Discount only for a lighthouse customer that provides a reference, engineering access, and a written case study approval. Price against protected workflow risk and reconciliation cost, not tokens or number of prompts.

### Acceptance criteria

Agree in writing before build:

- 100% of mediated test actions produce a receipt;
- 100% of injected timeout-before/after-commit scenarios classify correctly;
- duplicate retry never produces a second refund when the provider honors idempotency;
- altered, replayed, revoked-key, and stale receipts are rejected or marked indeterminate;
- post-state verification meets the agreed freshness SLA;
- no raw payment payload leaves the customer environment;
- at least one business metric improves against baseline;
- latency overhead is within the agreed workflow SLA;
- the customer’s auditor/security reviewer can run the verifier without the StateProof dashboard.

## Outreach strategy

### Target list

Build a list of 60 accounts:

- 20 fintech/payment companies;
- 15 marketplaces/commerce platforms;
- 10 B2B SaaS companies with automated billing;
- 10 insurers or claims administrators;
- 5 systems integrators or payment processors as referral partners.

For each account, identify four roles: workflow owner, platform champion, security/control approver, and procurement contact.

### Warm channels first

- former colleagues and engineering leaders;
- payment-processor and cloud-partner introductions;
- compliance/audit advisors who have seen refund incidents;
- founders of agent-support startups that need safe execution;
- specialized fintech and insurance accelerators;
- systems integrators that do not have a reusable post-state verification product.

### Message sequence

**Message 1 — incident question:**

> When an AI support agent receives a timeout after submitting a refund, how does your team determine whether the refund committed before retrying? We are testing a narrow control that verifies the authoritative post-state rather than trusting the tool response. Is this a current operational problem for your team?

**Message 2 — evidence:**

> We are not proposing another observability dashboard. The pilot binds policy, pre-state, idempotency key, provider operation ID, post-state, and an independently verifiable receipt. We can run it in your environment and compare it with your current reconciliation process.

**Message 3 — qualification:**

> If you have a named refund/payment workflow, an authoritative ledger/API, and a measurable reconciliation or duplicate-action cost, we can scope a 30-minute technical discovery. If not, we should not force a fit.

**Message 4 — pilot offer:**

> We can run a 90-day pilot with one connector, customer-controlled keys, adversarial failure injection, and written acceptance criteria. The pilot ends with a go/no-go production recommendation and a quantified comparison to your native controls.

## 90-day calendar

### Days 1–10: prepare the proof asset and pipeline

- finalize technical one-pager, threat model, receipt schema, and 5-minute demo;
- build the fake-provider failure harness;
- create the 60-account target list;
- conduct 10 warm introductions and 20 targeted outreach messages;
- schedule 8–10 discovery interviews;
- publish a technical note titled “Why HTTP 200 Is Not a Refund Receipt.”

**Gate:** at least 8 qualified conversations scheduled and 3 workflows with a named owner.

### Days 11–25: qualify pain and choose the connector

- interview payments/refunds, platform, security, and audit stakeholders;
- collect baseline volume, duplicate/reversal incidents, reconciliation time, and current controls;
- confirm the authoritative system and its idempotency/operation semantics;
- run a live failure-injection demo with two prospects;
- issue a short pilot proposal to the top three accounts.

**Gate:** at least 3 prospects confirm a measurable pain and 2 can provide technical access for a design partnership.

### Days 26–40: convert design partners

- sign two lightweight design-partner agreements;
- obtain architecture diagrams and test credentials;
- define success metrics and acceptance criteria;
- price the pilot and name the conversion owner;
- complete security questionnaire, data-flow diagram, and deployment plan.

**Gate:** one signed paid pilot or purchase-order path; one backup design partner.

### Days 41–60: deliver a proof in the customer environment

- deploy the connector in customer VPC or approved local environment;
- connect policy/invariant engine and customer key custody;
- mediate a non-production or low-risk refund workflow;
- reproduce timeout-before/after-commit, duplicate retry, conflict, stale read, and altered-receipt cases;
- hold weekly engineering/control-owner reviews.

**Gate:** customer accepts the evidence boundary, verifier, and first operational results.

### Days 61–75: run controlled comparison

- compare StateProof to current native controls;
- measure false-success detection, duplicate-action prevention, reconciliation time, latency, and evidence assembly;
- test bypass paths and document coverage limitations;
- conduct customer security and internal-audit review;
- write the preliminary ROI report.

**Gate:** at least one outcome metric improves without unacceptable latency or operational burden.

### Days 76–90: close conversion and create proof package

- deliver final pilot report;
- obtain production pricing and scope approval;
- ask for a reference quote or anonymized case study;
- secure the second paid pilot or expansion workflow;
- produce investor artifacts: demo, independent verifier output, failure matrix, customer letter, ROI baseline, security memo, and roadmap.

**Gate:** production conversion, second paid pilot, or a documented kill decision.

## Weekly operating dashboard

Track:

- accounts contacted;
- warm introductions;
- discovery meetings;
- qualified workflows;
- named economic buyers;
- technical design partners;
- pilot proposals;
- paid commitments;
- connector readiness;
- acceptance criteria signed;
- baseline metrics collected;
- adversarial tests passed;
- production conversion probability.

Do not count downloads, generic AI interest, conference leads, or positive comments as traction.

## Investor proof package after day 90

- one paid pilot contract;
- one independently verifiable receipt from a customer-controlled key;
- test report showing correct classification of all failure fixtures;
- measured improvement versus native controls;
- customer security/data-flow approval;
- quantified integration effort and latency overhead;
- second workflow hypothesis;
- explicit list of what StateProof does not claim.

## Kill or pivot rules

Kill the refund wedge if:

1. The connector cannot establish a trustworthy post-state boundary.
2. Customers say existing provider idempotency, workflow orchestration, policy, observability, and reconciliation already solve the job.
3. No buyer will pay after seeing the failure-injection proof.
4. The system adds material latency or support burden without reducing a measured cost.
5. Raw-data residency or security constraints make the gateway impossible to deploy.
6. Receipts are treated as another log rather than useful evidence.

If the technical proof works but refunds are not painful enough, pivot the same receipt/reconciliation core to insurance claims, provisioning, or regulated-record updates—not to a generic platform.
