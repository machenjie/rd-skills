# Kubernetes Source Contracts
Use this reference for Kubernetes API, controller, Helm, and Kustomize source
surfaces. It supports source validation only. It does not authorize cluster
mutation or production deployment.
Official pages in this reference were recorded as accessed on 2026-07-24.
## Kubernetes Objects, Controllers, and Operators
- Separate submitted desired state, observed state, status, and achieved external effects.
- Keep controller ownership, reconciliation idempotency, finalization, and failure status explicit.
- Inspect Server-Side Apply field ownership before forcing conflicts.
- Treat prune scope and API feature state as versioned deletion risks.
Primary sources:
- [Kubernetes objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
- [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Server-Side Apply](https://kubernetes.io/docs/reference/using-api/server-side-apply/)
- [Declarative object management](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)
Version limit: API availability, feature gates, admission, field ownership, CRD
conversion, and controller behavior depend on cluster and component versions.
A rendered object does not prove reconciliation.
## Helm
- Resolve chart dependencies and values precedence before inspecting the final render.
- Treat hooks and CRDs as lifecycle surfaces outside ordinary release resources.
- Keep rendered Secrets out of handoff evidence.
- Do not infer external-side-effect rollback from a Helm revision rollback.
Primary sources:
- [Helm upgrade](https://helm.sh/docs/helm/helm_upgrade/)
- [Helm rollback](https://helm.sh/docs/helm/helm_rollback/)
- [Chart hooks](https://helm.sh/docs/topics/charts_hooks/)
- [Custom resource definitions](https://helm.sh/docs/chart_best_practices/custom_resource_definitions/)
Version limit: the recorded command pages identify Helm 4.2.2 where stated.
Match the repository Helm, chart API, plugins, Kubernetes version, and CRD owner.
## Kustomize
- Validate the final selected overlay rather than a base in isolation.
- Inspect generators, name hashes, selectors, namespaces, labels, images, patches, and cross-cutting transforms.
- Compare rendered identity and ownership before treating the change as local.
Primary source:
- [Kustomize bases, overlays, and generators](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
Version limit: built-in and standalone Kustomize versions can differ. Rendering
does not prove admission, controller convergence, rollout safety, or live drift.
## Required Record
Return the Kubernetes and packaging versions, cluster target, selected overlay or
release, final rendered identities, field and controller owners, validation
evidence, deletion or secret risks, recovery owner, and live-state proof limits.
