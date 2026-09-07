# Placement and Ownership

Use this Reference only when structure, responsibility, ownership, reuse, or placement remains open.

## Professional Decision Rules

- When new structure or a boundary is proposed, place behavior with the owner of its reason to change and preserve the affected dependency direction.
- Reuse an abstraction only when its contract and ownership match current evidence.
- Similarity alone does not justify reuse.
- Skip reuse proof for owner-internal edits without structural change.
- When placement remains open, compare the smallest local design with broader alternatives against material change-locality, coupling, compatibility, operability, and deletion constraints.
- Require placement and ownership rationale only for proposed files, services, shared helpers, dependencies, public surfaces, or moved responsibilities that change structure.

## High-Value Gotchas

- Orphaned shared abstractions accumulate coupling.

## Execution Checklist

1. Trace current owner, consumers, and dependency direction.
2. Compare the smallest local placement with material alternatives.
4. **Analysis mode:** select placement and rejected alternatives.
6. Stop when evidence cannot support one placement.

## Placement Decision

- Only when structure or responsibility moves, state the owning module/service and public/private surface. Also state changed dependency edges and current reuse candidates. Name the selected local/reuse/new placement and why the strongest smaller alternative fails current constraints.
- When new structure, responsibility, or a boundary is proposed, require current owner and placement evidence plus a materially smaller alternative. Direct local placement, reuse, extension, composition, extraction, or a new boundary are candidates; choose from current contract, ownership, and change-locality evidence.

## Stop Conditions

- New shared abstractions, plugins, services, queues, registries, or interfaces require current consumers, owner, reversibility, and a rejected local alternative.
