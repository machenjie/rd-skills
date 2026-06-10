# Starter Repo

## Stack

Go or Java backend service with concurrent update tests.

## Initial State

`AccountUpdater` holds a mutex or synchronized block while it performs a
repository call and a network notification.

## Files

- `account/updater.go` or `src/main/java/account/AccountUpdater.java`
- `account/repository.*`
- `account/notifier.*`
- `tests/account_concurrency_test.*`

## Constraints

The benchmark rejects lock held across IO, missing timeout, missing deadlock
analysis, and serial-only tests.
