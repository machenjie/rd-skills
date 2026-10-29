# PHP Values, Errors, and Worker Lifetime

Load for PHP coercion, autoload, exception, or retained-worker behavior.
Skip package-manager commands without a PHP execution decision.

## Decision Rules

- Inspect both declared types and actual values entering the PHP boundary.
- Compare loose equality, strict equality, explicit conversion, and validation against the intended domain.
- Check numeric strings and invalid strings using the target PHP version's rules.
- Trace class resolution through the application's real entrypoint and autoload configuration.
- Exercise class-name and path casing on the target filesystem.
- Distinguish the intended `Exception`, `Error`, and `Throwable` handling boundaries.
- Preserve the original failure when cleanup also fails.
- Mark each mutable value as request, job, connection, or process state.
- Reset or isolate retained state at its owner when a worker processes another job.
- Verify resource closure on return, exception, shutdown, and worker restart paths.
- Use destructors according to their actual shutdown ordering.
- Verify timely external cleanup through the resource owner.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Numeric string, invalid string, zero, false, null | Boundary classification preserves distinct accepted and rejected values |
| Missing class or changed autoload order | Failure identifies the actual loader and class resolution |
| Two users processed by one retained worker | Second job cannot observe the first job request state |
| Exception after opening a stream or transaction | Cleanup preserves the primary error |
| Shutdown with dependent objects | Resource handling does not rely on an unsupported destructor order |

## Source Limits

- Bind conversion and lifecycle conclusions to the selected PHP version and execution model.

## Sources

- [PHP type conversion](https://www.php.net/manual/en/language.types.type-juggling.php)
- [PHP autoloading](https://www.php.net/manual/en/language.oop5.autoload.php)
- [PHP exceptions](https://www.php.net/manual/en/control-structures.try-catch.php)
- [PHP variable scope](https://www.php.net/manual/en/language.variables.scope.php)
- [PHP destruction](https://www.php.net/manual/en/language.oop5.decon.php)
