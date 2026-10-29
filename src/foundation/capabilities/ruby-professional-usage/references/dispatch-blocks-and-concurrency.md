# Ruby Dispatch, Blocks, and Concurrency

Load for dynamic receiver, nonlocal block control flow, cleanup, or concurrent Ruby state.
Skip unchanged Ruby code and package configuration without runtime consequences.

## Decision Rules

- Follow aliases, included modules, prepended modules, and visibility to the method actually invoked.
- Inspect `method_missing` and `respond_to_missing?` together when dynamic capability discovery matters.
- Check Proc and lambda arity against each call site.
- Trace `return` and `break` to their actual destination before extracting or storing a block.
- Verify whether an enumerator is lazy and whether repeated consumption repeats side effects.
- Keep rescue at the boundary that can classify or recover from the exception.
- Use `ensure` for owner cleanup without silently replacing the active failure.
- Distinguish `Thread#[]` fiber-local values from explicit thread variables.
- Establish how child threads publish failures and stop before their owner exits.
- Test retained worker state across requests or jobs, not only isolated invocations.
- Verify engine-specific concurrency behavior instead of treating one implementation's lock as an application invariant.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Stored non-lambda Proc executes after its method returned | Nonlocal return can raise LocalJumpError |
| Lambda receives unexpected arguments | Its argument contract differs from an ordinary Proc |
| Exception or early return inside a resource block | Cleanup preserves the material failure |
| Fiber switches within a worker thread | Context follows its intended storage scope |
| Background thread raises before join | The owner observes failure |
| Lazy enumeration is consumed twice | Repeated effects match the accepted contract |

## Source Limits

- Use the target Ruby version when these rules differ.

## Sources

- [Ruby 3.4 Proc semantics](https://docs.ruby-lang.org/en/3.4/Proc.html)
- [Ruby 3.4 exceptions](https://docs.ruby-lang.org/en/3.4/syntax/exceptions_rdoc.html)
- [Ruby 3.4 threads](https://docs.ruby-lang.org/en/3.4/Thread.html)
