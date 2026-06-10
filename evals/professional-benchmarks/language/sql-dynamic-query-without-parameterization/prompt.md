Review this SQL change:

The backend builds `WHERE name = '${query}'` and `ORDER BY ${sort}` from request
parameters. There is no parameter binding, no tenant predicate test, no query
plan, and no integration test against a real database.
