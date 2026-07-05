# Starter Repo

## Stack

Python 3.11 webhook controller with request headers, raw body access, shipment
service, event store abstraction, and pytest tests. The verifier should use
standard HMAC primitives.

## Initial State

The shipping webhook controller parses JSON and calls the shipment service for
every request. There is no signature verifier, no timestamp check, no durable
event id store, and only a generic success test.

## Files

- `shipping/webhook_controller.py` receives headers and body.
- `shipping/webhook_verifier.py` contains a placeholder verifier.
- `shipping/event_store.py` records processed provider event ids.
- `shipping/service.py` updates shipment status.
- `tests/test_shipping_webhook.py` covers one valid JSON body.

## Constraints

Keep provider header names configurable in one place. Verification must happen
before shipment updates. The event store contract should support transactional
deduplication when backed by a relational database.