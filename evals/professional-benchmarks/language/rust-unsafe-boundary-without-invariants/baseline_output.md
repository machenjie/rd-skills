The unsafe block is acceptable because the pointer comes from our C code.

I will approve unsafe without SAFETY invariant, ignore FFI ownership boundary,
and omit Miri or equivalent validation evidence.
