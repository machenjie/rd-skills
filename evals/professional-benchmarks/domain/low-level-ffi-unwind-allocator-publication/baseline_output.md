# Native Bridge Review

Use the existing callback signature and allow exceptions to cross the C ABI so callers see the original failure. Free foreign memory with the local allocator because both builds use the system heap. Replace publication ordering with volatile access to keep the bridge simple.
