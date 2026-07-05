Selected stage: code-review.
Selected professional skill: ai-code-review-refactor.
Selected capabilities: cpp-professional-usage.

Hidden risks: C++ raw pointer lifetime without RAII; dangling pointer ownership unclear; sanitizer evidence missing.

Inspected boundaries: buffer ownership, destructor free path, caller lifetime contract, RAII wrapper choice, FFI boundary, ABI surface, and sanitizer lane.

Evidence required: ownership and lifetime model; RAII or smart pointer decision; sanitizer or static analysis evidence.

Output obligations covered: ownership model evidence; validation evidence for lifetime safety; what evidence proves and does not prove; residual native safety risk owner.

Validation command: `ctest -R parser_lifetime && ASAN_OPTIONS=detect_leaks=1 ctest -R parser_lifetime` (not run in fixture; expected outcome is lifetime and leak sanitizer output).
What evidence proves: the inspected parser ownership path has a defined lifetime model and sanitizer coverage.
What evidence does not prove: all compiler optimizations, downstream binary compatibility, or every FFI caller.

Residual risk: ABI consumers still need compatibility review; owner: architecture-impact-reviewer.
Next gate: low-level-systems-extension if exported ABI changes.
