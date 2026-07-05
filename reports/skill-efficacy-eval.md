# Skill Efficacy Evaluation

- Generated: 2026-07-04T06:07:14.757760+00:00
- Benchmarks checked: 3
- Warning count: 3
- Measured comparisons: 0
- Structural fixtures: 3
- Average efficacy score: 100.00/100
- Score model: 100-point skill efficacy rubric from docs/skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md

## Scores

| Benchmark | Capability | Score | Status | Evidence Level | Warnings |
| --- | --- | ---: | --- | --- | ---: |
| `agent-tool-permission-sandbox-command` | `agent-tool-permission-sandbox` | 100/100 | structural-pass | structural fixture | 1 |
| `plan-execution-consistency-drift` | `plan-execution-consistency` | 100/100 | structural-pass | structural fixture | 1 |
| `repository-context-map-placement` | `repository-context-map` | 100/100 | structural-pass | structural fixture | 1 |

## Dimension Detail

### `evals/skill-efficacy/agent-tool-permission-sandbox-command.yaml`

| Dimension | Score |
| --- | ---: |
| structure_contract | 20/20 |
| semantic_behavior_delta | 25/25 |
| reference_efficiency | 20/20 |
| measurement_evidence | 20/20 |
| skill_only_closure | 15/15 |

Warnings:
- advisory: measured_efficacy_not_collected (measurement_evidence) - fixture is structural and does not prove measured runtime improvement

### `evals/skill-efficacy/plan-execution-consistency-drift.yaml`

| Dimension | Score |
| --- | ---: |
| structure_contract | 20/20 |
| semantic_behavior_delta | 25/25 |
| reference_efficiency | 20/20 |
| measurement_evidence | 20/20 |
| skill_only_closure | 15/15 |

Warnings:
- advisory: measured_efficacy_not_collected (measurement_evidence) - fixture is structural and does not prove measured runtime improvement

### `evals/skill-efficacy/repository-context-map-placement.yaml`

| Dimension | Score |
| --- | ---: |
| structure_contract | 20/20 |
| semantic_behavior_delta | 25/25 |
| reference_efficiency | 20/20 |
| measurement_evidence | 20/20 |
| skill_only_closure | 15/15 |

Warnings:
- advisory: measured_efficacy_not_collected (measurement_evidence) - fixture is structural and does not prove measured runtime improvement
