# Scientific Solver Validity and Reproducibility

Load for model assumptions, solver applicability, convergence, conserved quantities, or stochastic scientific claims.
Skip numeric formatting and calculations without a scientific model or solver decision.

## Decision Rules

- State the scientific question and the assumptions that connect it to the implemented equations.
- Validate units, shape, initial conditions, boundary conditions, and physical parameter ranges.
- Match solver assumptions to the problem, including stiffness, constraints, smoothness, and scale where relevant.
- Keep the accepted numerical error budget separate from model error and measurement uncertainty.
- Inspect convergence status, termination reason, iteration limits, and incomplete output.
- Compare against an analytic limit, trusted reference solution, or independently justified benchmark.
- Check applicable conservation laws and constraint residuals across the simulated interval.
- Use refinement or sensitivity studies to distinguish numerical artifacts from meaningful model behavior.
- Identify the sampling unit, dependence, random design, and uncertainty calculation for stochastic experiments.
- Preserve data, parameters, code, environment, solver settings, and relevant random state for reproduction.
- Report unsupported regimes rather than extrapolating a solver success beyond its tested domain.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Units or axes are inconsistent | Input validation rejects the wrong physical problem |
| Iteration limit is reached with finite output | Result is marked nonconverged or incomplete |
| Solver reports success but conservation drifts | Invariant evidence blocks unsupported validity claims |
| Stable solution uses the wrong boundary conditions | Model review rejects a numerically correct answer to the wrong problem |
| Same seed runs in another environment | Reproducibility claim records the actual environment limits |
| Local error estimate is small | Model validity and global behavior still require independent evidence |

## Proof Limits

- A solver local-error estimate is not proof of model correctness, global accuracy, or physical applicability.
- Reuse the selected numerical-correctness guidance for conditioning, precision, and tolerance decisions.

## Sources

- [SciPy solve_ivp contract](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
