Review this Go change:

`handleSubscribe` starts a goroutine per request to stream events. The goroutine
does not observe `ctx.Done()`, drops errors on the floor, and is not covered by
`go test -race`. Cancelled clients leak goroutines and connections.
