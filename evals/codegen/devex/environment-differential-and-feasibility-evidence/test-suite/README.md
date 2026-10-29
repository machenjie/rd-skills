# Test Suite

## Required Checks

- Normalize effective environment facts and preserve causal uncertainty.
- Admit only isolated, linked, reproduced interventions.
- Compare fixed experiment inputs, versions, factors, and critical boundaries.
- Compute resource totals and obey planned stops.
- Keep every result within prototype-only limits.

## Fixtures

fixtures/passing implements the contract. fixtures/delta-is-cause changes one mechanism: it accepts an observed delta without an intervention. starter-repo remains incomplete.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Eight methods distinguish toolchain, application, and configuration causes from hypotheses. They reject cleanup claims, uncontrolled changes, mock boundaries, invalid measurements, early stops, and continued work after exhaustion.

The suite derives expected differences, ratios, resource sums, and ordering independently. Default smoke proves starter rejection only. Execute passing and faulty candidates separately.
