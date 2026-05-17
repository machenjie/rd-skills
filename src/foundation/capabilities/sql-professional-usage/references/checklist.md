# SQL Professional Usage Checklist

- Parameterize every value derived from user or external input.
- Check execution plan for non-trivial queries.
- Confirm indexes match filters, joins, ordering, and write cost.
- Review transaction scope, isolation, locks, and migration compatibility.
- Make NULL, timezone, and monetary precision semantics explicit.
- Use stable bounded pagination.
- Avoid unbounded scans in user-facing paths.
- Add tests or fixtures for edge cases and migration behavior.
