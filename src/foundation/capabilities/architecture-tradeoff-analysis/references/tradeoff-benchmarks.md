# Architecture Tradeoff Comparison Patterns

Load this reference when feasible options need a comparison method and current evidence does not already determine the choice. It supplies mechanism-neutral comparison shapes, not a framework catalog.

| Comparison element | Qualitative form | Conditional numeric form |
| --- | --- | --- |
| Hard constraint | Feasible, disqualified, or unresolved with authority and evidence | Use a measured boundary only when the constraint itself is numeric; never average a failure into a total |
| Preference | Better, worse, similar, or uncertain under the named outcome | Use a common scale only when its meaning, source, and direction are shared across feasible options |
| Material consequence | Benefit, cost, risk, obligation, or future option created/closed | Quantify only when current measurement or an explicit model supplies comparable units and uncertainty |
| Reversibility and exit | Easier/harder to unwind; dependencies and retained obligations | Estimate ranges only when scope, assumptions, authority, and validation basis are stated |
| Evidence strength | Observed, authoritative, modeled, assumed, or unavailable | Do not convert evidence quality into false arithmetic precision |
| Assumption sensitivity | Selection stable, unstable, or unresolved under plausible change | Show whether supported input ranges change feasibility or the selected option |

Start with qualitative comparison. Use numeric scoring only when feasible options share an evidence-backed scale and the result remains interpretable under uncertainty; define the scale before comparison and show sensitivity. Do not invent weights, placeholder values, or totals to make an already preferred option appear objective.

A disqualified option remains outside preference comparison until evidence shows the hard constraint no longer applies. If hard constraints leave one feasible path, report the constraint result and proof limits instead of manufacturing a tradeoff matrix.

Proof scope: these patterns do not establish feasibility, ownership, graph completeness, exit execution, security, reliability, cost accuracy, or release readiness. Require fresh evidence from each owning boundary before approving the decision.
