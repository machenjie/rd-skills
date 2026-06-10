# Architecture Tradeoff Benchmarks

Load this reference only for architecture review, ADR preparation, or L4/L5 changes.

## Benchmark Anchors

Anchor against: **ADRs (Michael Nygard, 2011)** and the MADR template (markdown ADR), **Lightweight RFCs** (Oxide Computer / Squarespace / Rust RFC process), **C4 model** for context/container diagrams supporting the decision, **DACI / RAPID** decision-rights frameworks, **Risk registers** (ISO 31000), **NASA Technical Risk Management Handbook**, **Cynefin framework** (Snowden) for matching decision approach to problem domain (simple/complicated/complex/chaotic), **Wardley Mapping** for evolution-aware tradeoffs, **Cost of Delay** (Reinertsen) for time-value weighting, **Bezos Type-1/Type-2** reversibility classification, **Architecture Fitness Functions** (Ford/Parsons/Kua), **Decision Records** practice (adr.github.io), **WRAP framework** (Heath/Heath: Widen options, Reality-test, Attain distance, Prepare to be wrong), **Eisenhower / RICE** prioritization where alternatives must be ranked, **DORA** outcomes as quality lens. For irreversible technology choices, apply **Lindy effect** reasoning to bet on technologies with proven longevity.

## Decision-Force Catalog

Use this canonical list, then rank by weight (1 = decisive, 5 = nice to have). Omit forces that do not apply, but state so.

| Force | Probe question |
| --- | --- |
| Delivery speed (time-to-market) | How many weeks/months does each option add or save? |
| Cognitive load | Can the existing team operate this without specialist hiring? |
| Operational cost | What does this cost at projected 12-month scale (infra + people)? |
| Reliability / availability | What SLO does each option support, with what investment? |
| Performance (latency, throughput) | Does each option meet the p95/p99 budget under projected load? |
| Security posture | Does each option reduce or expand attack surface and trust boundaries? |
| Privacy / compliance | Does each option simplify or complicate PCI/HIPAA/GDPR scope and residency? |
| Reversibility | How costly is exit? Days, weeks, years? |
| Vendor lock-in | Is the data/format/contract portable? |
| Talent availability | Can we hire for this in our market in 6 months? |
| Ecosystem health | Library age, maintainer count, release cadence, CVE backlog |
| Coupling impact | Does this widen or narrow the blast radius? |
| Migration cost | What does it cost to get from current state to target state? |
| Testability | Can each option be tested without production-only fidelity? |
| Observability | Are metrics, logs, traces, debugging tools mature? |
| Future flexibility | Does this preserve or close downstream options? |

## Options Matrix Template

| Force (weight) | Option A | Option B | Option C |
| --- | --- | --- | --- |
| Delivery speed (4) | 6 weeks | 12 weeks | 4 weeks |
| Operational cost (5) | $X/mo | $Y/mo | $Z/mo |
| Reversibility (3) | Type 2 | Type 1 | Type 2 |
| Compliance (5) | In scope simplification | Neutral | Adds scope |
| ... | ... | ... | ... |
| **Weighted score** | | | |
| **Disqualifying constraint** | - | residual auth risk | cost > budget |

Weighting must be set **before** scoring, not adjusted to make a preferred option win.

## Decision Tree: Decision Approach By Cynefin Domain

```
What is the nature of the problem?
├─ Simple (best practice exists)        → Apply best practice; lightweight ADR; reviewer = peer.
├─ Complicated (analyzable, experts)    → Full tradeoff analysis; multiple alternatives; reviewer = senior architect.
├─ Complex (emergent, requires probing) → Run experiments (spikes, prototypes) before committing; reversible design;
│                                          design fitness functions; review after first production data.
└─ Chaotic (incident, no time to model) → Act → sense → respond; record post-hoc; revisit when stable.
```
