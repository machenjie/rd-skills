# Security Checks

## Threat Surface

The feature may persist dismissal state in browser storage and render
server-provided billing metadata.

## Required Checks

- Do not store sensitive billing data in localStorage or sessionStorage.
- Render copy and metadata as text, not raw HTML.
- Keep billing API or persistence calls out of generic shared UI components.

## Rejection Cases

Reject solutions that store invoice identifiers or account details in browser
storage, render raw HTML, or move billing data access into shared UI.
