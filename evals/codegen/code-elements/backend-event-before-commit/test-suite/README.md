# Test Suite

## Required Checks

- Verify event publication happens after commit.
- Verify cache mutation happens after commit.
- Verify commit failure publishes no event and writes no cache.
- Verify no duplicate events are created.
- Execute the actual backend regression test; smoke mode must observe the
  starter failure, and candidate mode must pass.

## Fixtures

Use successful commit, commit failure, publish failure, and duplicate command fixtures.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Event before commit must fail review.
- Cache from uncommitted state must fail review.
- Commit failure must not publish or update cache.
