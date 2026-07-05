# Starter Repo

## Stack

Python, Go, or TypeScript backend integration code with adapter tests.

## Initial State

`CustomerRepository` and `PartnerAdapter` create HTTP, DB, or SDK clients inside
each operation and do not consistently close response bodies or streams.

## Files

- `customers/repository.*`
- `partners/adapter.*`
- `infrastructure/clientFactory.*`
- `tests/integration/test_client_lifecycle.*`

## Constraints

The benchmark rejects per-operation client construction, response body leaks,
missing pool sizing, and hidden IO behind repository or adapter APIs.
