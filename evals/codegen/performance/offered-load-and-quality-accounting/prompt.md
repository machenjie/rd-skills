# Benchmark Prompt

## Task

Complete the bounded fixture adapters in `subject.py` for deterministic validation. This is test infrastructure, not product implementation or a new runtime.

## Context

The accepted contracts are fixed below. Candidate functions consume raw records or controlled collaborators; assertions derive expected behavior independently.

## Requirements

- `analyse_load(planned, observations)` receives planned arrival times indexed by request ID. Observations contain `id`, `start`, `end`, and `outcome`.
- Count intended, sent, unsent, success, rejected, timeout, and pending work separately. Missing observations and records without a start are unsent.
- Return queue delay as start minus planned arrival. Return terminal planned latency as end minus planned arrival and service latency as end minus start, keyed by request ID.
- Reject duplicate or unknown IDs, starts before schedule, ends before starts, terminal results without a start, and unfinished work with a terminal result.
- `configuration_failures(measurement, policy, mode)` evaluates `min_quality`, `max_p99_ms`, and `max_unit_cost` independently of throughput.
- Hosted evidence includes `input_tokens`, `output_tokens`, `quota`, and `billed_after_cancel` within `measurement['hosted']`.
- Self-hosted evidence includes `prefill_ms`, `decode_ms`, `weights_bytes`, `kv_bytes`, and `device_bytes` within `measurement['self_hosted']`. Weights plus KV exceeding device memory fails this bounded capacity model.
- Return failed dimensions as a set using `quality`, `tail-latency`, `cost`, `hosted-evidence`, `self-hosted-evidence`, and `device-memory`. Reject unknown modes.

## Constraints

Use Python standard-library code without network, real clocks, or external services. Do not edit assertions or add expected-answer fields to input records.

## Deliverables

Implement the callable interfaces and explain the unproved boundaries. Preserve the distinction between supplied policy and universal behavior.

## Completion Evidence

Run passing-candidate assertions and reject the incomplete starter and the single-mechanism faulty control. This case neither generates load nor proves real latency, provider billing, GPU capacity, production quality, or model performance.
