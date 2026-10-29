# Artifact Consumer Verification

- Choose a consumer that exercises the changed public entrypoint and the repaired failure path.
- Build from declared source and inspect included files, exports, metadata, and runtime dependencies.
- Install or load the built artifact outside the repository import path.
- Pin the tested package, runtime, platform, and consumer invocation.
- Verify returned values, errors, resources, process exit, and cleanup where the change affects them.
- Compare the unchanged public contract across supported versions or platforms only when the compatibility claim spans them.
- Include a failure control that the old artifact cannot satisfy.
- Report a missing runtime or platform explicitly; a source test does not fill that evidence gap.

| Defect | Consumer check | False success to reject |
|---|---|---|
| Internal algorithm returns an incorrect boundary value | Call the installed package with that boundary | Passing unrelated source tests |
| Resource remains open after cancellation | Observe cleanup through the public operation | Successful package installation alone |
| CLI omits a runtime file | Execute the built command outside the checkout | Importing files directly from source |
| Public cancellation semantics must change | Hand off the contract decision | Treating observable changes as internal repair |
