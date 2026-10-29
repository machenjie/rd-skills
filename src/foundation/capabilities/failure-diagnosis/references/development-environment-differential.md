# Development Environment Differential

- Compare the same invocation, source revision, input, and expected outcome across passing and failing environments.
- Resolve the actual executable, PATH order, working directory, runtime, architecture, compiler, and toolchain.
- Trace environment variables to their source and override order without exposing secrets.
- Compare resolved dependency graphs and generated artifacts, not only manifest text.
- Check certificates, proxy routes, ports, filesystem permissions, and required external services when evidence implicates them.
- Reproduce in a clean environment with declared inputs.
- Change one discriminating input and retest the causal prediction.
- Classify the cause as application behavior, toolchain behavior, or environment configuration only after verifying that distinction.
- Preserve failure evidence before reinstalling, clearing caches, or replacing lockfiles.
- Return the minimal causal difference, correction, and remaining environment limits.

| Observation | Discriminating check |
|---|---|
| Local pass, CI failure | Compare executable identity, toolchain, graph, working directory, and generated inputs |
| One developer fails | Compare declared environment sources and service reachability |
| Clean checkout fails | Identify ambient files, undeclared tools, or missing bootstrap outputs |
| Reinstall appears to fix it | Identify which dependency or cached input changed before claiming cause |
