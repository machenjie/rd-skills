# PowerShell Pipeline, Error, And Native Contracts

Use this checklist when object flow, errors, native processes, or text/byte boundaries can change automation outcomes.

## Boundary Checklist

- **Pipeline object:** record emitted .NET types, scalar/collection cardinality, automatic enumeration, `ByValue`/`ByPropertyName` binding, null/empty behavior, and where formatting begins.
- **Streams:** assign success, error, warning, verbose, debug, information, and progress consumers; define redirection without confusing stderr with a PowerShell error record.
- **PowerShell error:** classify terminating and non-terminating cases, local `-ErrorAction` versus preference scope, `try/catch/finally`, preserved `ErrorRecord`, retryability, and final exit.
- **Native argument:** construct an argument vector for the actual edition/OS and prove spaces, quotes, empty values, wildcards, and secret redaction at the invoked program.
- **Native result:** capture stdout/stderr or bytes intentionally, inspect `$LASTEXITCODE` immediately, define accepted codes, and translate timeout/cancellation/failure once.
- **Encoding:** state source, destination, BOM, newline, console/process encoding, append behavior, and the exact cmdlet or native boundary selecting it.
- **Function contract:** use advanced-function parameter validation and pipeline methods only when their binding/cardinality behavior is tested; emit data rather than display formatting.

## Failure Probes

- Pipe zero, one, and many typed objects, plus an object whose property name binds unexpectedly.
- Generate terminating and non-terminating errors under the actual preference values and verify the process exit observed by automation.
- Invoke the native tool with spaces, quotes, empty arguments, nonzero accepted/rejected codes, separate stderr, and cancellation.
- Round-trip non-ASCII text and raw bytes through the exact PowerShell edition, cmdlet, redirection, and native pipeline used in production.

## Primary Sources

- [about_Pipelines](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_pipelines?view=powershell-7.6)
- [about_CommonParameters](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_commonparameters?view=powershell-7.6)
- [about_Preference_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables?view=powershell-7.6)
- [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.6)
- [about_Parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.6)
- [about_Quoting_Rules](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-7.6)
- [about_Character_Encoding](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding?view=powershell-7.6)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Microsoft Learn is rolling; record `$PSVersionTable`, edition, OS, host, native-tool version, effective preferences, and the selected `view` limitation.
- Windows PowerShell 5.1 and PowerShell 7 differ in encoding, native parsing, and pipeline behavior; do not generalize evidence from one edition or OS.
- Documentation does not prove a native program's argument parser, accepted exit codes, byte/text protocol, locale, or the caller's interpretation.

## Required Record

- Record object/cardinality and stream contracts, effective error preferences, native arguments and exit mapping, encoding/edition evidence, exercised failures, proof limits, and residual risk.
