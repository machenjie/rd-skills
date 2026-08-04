# AI Security Review

Primary Professional Skill: `security-privacy-gate`  
Selected Domain Skill: `ai-product-extension`

## Hidden risks

- retrieval can return chunks after source authorization is revoked
- retrieved prompt injection can compose allowed tools into an unauthorized effect
- tool calls can execute with ambient service authority instead of the requesting principal

## Required evidence

- cross-principal and stale-revocation retrieval negative tests
- indirect prompt-injection test against trusted instruction precedence
- tool-call principal scope argument validation confirmation and audit proof

## Handoff

- security verdict and blocked abuse paths
- selected retrieval permission and tool-authority controls
- evaluation gaps fallback and residual owner

Verdict: block release until retrieval is principal-scoped, revocation reaches every serving index, untrusted context remains structurally separated, and each tool request is authorized as the requesting actor.
