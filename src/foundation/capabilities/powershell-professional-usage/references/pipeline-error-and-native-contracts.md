# PowerShell Pipeline, Error, And Native Contracts

Load when object flow, errors, native processes, or text/byte boundaries can change automation outcomes.

## Boundary Decision Map

| Boundary | Required decision |
| --- | --- |
| Object | Bind emitted .NET type, cardinality/enumeration, parameter binding, null/empty behavior, and formatting boundary. |
| Streams/errors | Assign stream consumers; classify terminating and non-terminating cases; bind `-ErrorAction`, preference scope, catch/finally, `ErrorRecord`, retryability, and final exit. |
| Native | Bind argument vector to edition/OS; prove quoting/empty/wildcards/redaction, immediate `$LASTEXITCODE`, accepted codes, timeout, cancellation, and one failure translation. |
| Encoding/function | Bind text/byte source, destination, BOM/newline, console/process encoding and append behavior; test advanced-function binding/cardinality before use. |

## Failure Probes

- Exercise zero/one/many/null objects, unexpected property binding, effective error preferences, and caller-observed exit.
- Exercise native quoting, empty arguments, accepted/rejected codes, separate stderr, timeout, and cancellation.
- Round-trip non-ASCII text and bytes through the exact edition, cmdlet, redirection, and native boundary.

## Primary Sources

- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_pipelines?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_commonparameters?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding?view=powershell-7.6

Official pages were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Record PowerShell edition/version, OS, host, native-tool version, effective preferences, and selected documentation view.
- Do not generalize Windows PowerShell 5.1 evidence to PowerShell 7, or one edition/OS to another.
- Documentation does not prove a native parser, accepted codes, byte/text protocol, locale, or caller interpretation.

## Required Record

Record object/cardinality and stream contracts, error preferences, native arguments/exit mapping, encoding/edition evidence, exercised failures, limits, and residual risk.

## Anti-Patterns

- Success flags, text conversion, command strings, syntax portability, and blind reruns do not prove contracts.
