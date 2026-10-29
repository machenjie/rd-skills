# Review Rubric

## Passing Standard

The fixture adapters satisfy their accepted contracts under direct function and trace assertions.

## Scoring

Assess intended versus actual arrivals, queue delay, planned and service latency, terminal outcomes, pending work, explicit policies, and hosted versus self-hosted inputs.

## Automatic Failure Conditions

Discarding unsent arrivals or measuring latency only after actual start. Approving higher throughput despite violated quality, tail-latency, or cost constraints.

## Reviewer Notes

This case neither generates load nor proves real latency, provider billing, GPU capacity, production quality, or model performance. Static definitions and starter rejection do not replace a passing-candidate run.
