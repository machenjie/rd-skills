Review this C++ change:

A parser stores a raw pointer to a caller-owned buffer and frees it in the
destructor. The code has no RAII wrapper, no ownership comment, no sanitizer
test, and no statement about ABI or FFI callers.
