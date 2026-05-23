# 2026-05 Cloud Component Skill Audit

## Baseline

Baseline validation before changes passed on 2026-05-23 with the full core validation chain:

- `python3 scripts/validate-skills.py`
- `python3 scripts/validate-capabilities.py`
- `python3 scripts/validate-domain-extensions.py`
- `python3 scripts/validate-registry.py`
- `python3 scripts/validate-skill-body-links.py`
- `python3 scripts/eval-routing.py`
- `python3 scripts/validate-codegen-benchmarks.py`
- `python3 scripts/run-codegen-benchmarks.py --limit 3`
- `python3 scripts/build.py --profile recommended`
- `python3 scripts/build.py --profile full`
- `python3 scripts/build.py --profile dev`
- `python3 scripts/validate-installation.py`

Initial coverage notes:

- Redis: covered by `cache-design`, routing trigger weak.
- Kafka: covered by `message-queue-design` + `bigdata-product-extension`, routing trigger weak.
- K8s: covered by `kubernetes-gateway`, routing trigger medium.
- Helm: weak, only lightly mentioned.
- Spark: covered by `bigdata-product-extension`, routing trigger weak.

## Updates

- Redis: explicit routing added.
- Kafka: explicit routing added.
- K8s: resource-name routing added.
- Helm: professional content added under `kubernetes-gateway`/`ci-cd`/`delivery-release-gate`.
- Spark: explicit routing added.
