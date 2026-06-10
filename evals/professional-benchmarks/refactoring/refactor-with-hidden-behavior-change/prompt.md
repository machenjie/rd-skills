Review this refactor proposal:

A service method `OrderService.applyPromotion()` was split into
`PromotionPolicy` and the old helper was deleted. The author says this is only a
behavior-preserving cleanup, but the diff changes a `null` return into an empty
array, maps validation failures to a different exception type, and does not show
caller scans, characterization tests, or a rollback path for the deleted helper.

Decide whether the refactor is acceptable and state the evidence required before
handoff.
