Review this Rust change:

A new `unsafe` block converts a raw FFI buffer into a slice. There is no
`// SAFETY:` comment, no ownership invariant, no lifetime/aliasing statement,
and no Miri or FFI panic-boundary test.
