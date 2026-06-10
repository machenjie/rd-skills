This is a clean refactor and can merge.

I will call behavior change a refactor without approval because returning an
empty list is close enough to returning null. I will also change public API or
error semantics without evidence and delete old path without proving callers
migrated.

Existing tests should catch anything important.
