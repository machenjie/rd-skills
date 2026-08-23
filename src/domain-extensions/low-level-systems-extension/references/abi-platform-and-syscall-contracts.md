# ABI, Platform, and Syscall Contracts

Use this Reference only for the named low-level abi-platform-and-syscall-contracts decision.

## Decision Rules

- Make ABI representation explicit: calling convention, symbol and version contract, struct and union layout, packing, alignment, padding, bit fields, endianness, word size, and serialization compatibility for deployed consumers.
- Cover supported OS, architecture, compiler, runtime, filesystem, network-stack, privilege, and permission differences that affect behavior or compatibility.
- Handle partial I/O, interruption, would-block results, timeout, cancellation, error mapping, kernel and user length validation, privilege changes, and sandbox behavior under its syscall contract.
