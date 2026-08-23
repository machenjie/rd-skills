# Package Dependency Management Checklist

- **Justify capability before package choice.** Compare reuse already present, platform support, implementation cost, maintenance status, transitive surface, runtime weight, license, and security consequence against the task-local need.
- State why the dependency change is needed and what alternatives were rejected.
- Review direct and transitive package changes.
- Verify lockfile integrity and reproducible install command.
- Check vulnerability, license, provenance, maintenance, and install script risks.
- Review native extensions and platform compatibility.
- Confirm CI, build, runtime, and deployment compatibility.
- Define owner and expiry for accepted exceptions.
- Add tests for behavior supplied by the dependency.
