# Bounded Observation

Use only when an analysis question needs a specific executable observation or another agent needs a bounded check. A normal implementation agent runs its own discovery and validation directly.

State the question, authorized operation and targets, and observable result needed to resolve it. Preserve Host permissions and the user-authorized write boundary. For a no-edit observation, verify relevant workspace state before and after; unexpected mutation invalidates the no-edit claim.

Return the actual operation, outcome, evidence, and proof limits. Partial observations remain partial. Never invent tool failures, retry unchanged after two failures, or reset the same question by renaming its assignment. No separate state engine, signatures, or private evidence storage.
