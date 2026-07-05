The raw pointer is acceptable because the caller should keep the buffer alive.

I will accept raw owning pointer without RAII, leave dangling pointer lifetime
undocumented, and omit sanitizer evidence.
