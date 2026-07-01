Update the enum, serializer, and tests for the new `SUSPENDED` status.

This treats status enum edits as serialization-only and skips allowed and
forbidden transition evidence.
