# Scorecard

This handwritten table defines release expectations. It is not generated
status and not a current-tree pass report. Current status comes only from fresh
producer output and the generated or captured artifacts indexed in
[Reports](../reports/README.md).

| Dimension | Required evidence | Release expectation |
| --- | --- | --- |
| Registries | four registry validators | 1 Control, 26 Professional, 150 Foundation, and 13 Domain Skills: 190 total and 189 non-Control |
| Runtime and Agent Profiles | build, Profile, and prompt validators | one Runtime with 27 top-level Skills, exactly four bounded Agent Profiles, and one authoritative control prompt |
| Contracts | task-contract validator | Markdown Direct Task, Engineering Brief, Task DAG, and Review Handoff |
| Routing | deterministic routing evaluator | one primary Professional Skill per task; 233 canonical entries and 62 capability entries; 429 admissions are 105 Professional, 276 Foundation, and 48 Domain; the Foundation projection covers 141 unique Foundation Skills in the 163-entry Layer 3 catalog |
| Capability coverage | 125-entry matrix and deterministic coverage validators | 125 entries classify as 81 covered, 39 partial, 0 missing, and 5 intentionally unsupported; covered is catalog/routing evidence, not Professional Completeness |
| Content | link, size, audit, readability, and professionalism checks | no broken references, release-blocking readability disposition, or unresolved professional defect |
| Tests | full unit suite | all applicable tests pass on the final material edit |
| Code generation | definition and harness validation | checked-in harnesses run and assertions reject incomplete starters |
| Build | fixed Runtime plus temporary Layer 3 completeness validator | 27/154/9 top-level/targeted/routing-only delivery; 163 Foundation/Domain sources remain complete; no Layer 3 top-level or packaged surface |
| Installation | simulated installation validator and doctor | expected host-specific Skills/Profiles and no obsolete managed residue |

Record producer command, source commit or diff state, freshness, skipped checks,
and proof limits in the release handoff. Any skipped check, stale report, or
partial suite is explicit unverified scope. Do not convert this expectations
table into a manual green status.

The scorecard cannot prove real-host Profile startup, wall-clock performance,
production accuracy, provider behavior, or installed user experience. See
[Validation](VALIDATION.md), [Benchmarks](BENCHMARKS.md), and
[Release](RELEASE.md).
