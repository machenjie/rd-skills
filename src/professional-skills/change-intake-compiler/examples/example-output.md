# Example Output

Change Request: Prevent archived projects from appearing in active project search.

Current behavior: Archived projects are returned by the active search endpoint.

Desired behavior: Active search excludes archived projects unless an explicit include flag is used.

Non-goals: No redesign of archival workflow.

Missing information: Whether existing clients depend on archived results.

Completion signal: Regression test proves archived records are excluded by default and included only with the flag.
