# License Decision

This repository currently records proprietary license metadata in `pyproject.toml`
and has no root `LICENSE` file. That is intentional until the repository owner
chooses a license.

## Current Status

- Repository/tooling license metadata: `Proprietary`.
- Root `LICENSE`: not present.
- Open-source publication status: blocked by owner decision.
- Contribution licensing confirmation: not confirmed.
- Private vulnerability reporting or private security contact: not confirmed.

## Why This Blocks Public Open-Source Release

Public open-source release requires a clear legal grant. Without a selected
license and exact license text, users and contributors cannot know what rights
they have. A repository should not be described as open source while package
metadata remains proprietary or while contribution and security reporting paths
are unresolved.

## How To Complete The Decision

The owner must choose one license identifier and update
`config/open-source-release.yaml`.

Allowed example values:

- `MIT`
- `Apache-2.0`
- `BSD-3-Clause`
- `MPL-2.0`
- `GPL-3.0-only`
- `AGPL-3.0-only`

After choosing, copy the standard license text exactly from an authoritative
source such as the SPDX license text, the OSI license page, or the license
steward. Do not paraphrase, summarize, or rewrite standard license text.

## Files To Change After Owner Selection

1. Add root `LICENSE` with the exact selected license text.
2. Update `pyproject.toml` license metadata from `Proprietary` to the selected
   non-proprietary license metadata.
3. Update `config/open-source-release.yaml`:
   - set `selected_license` to the chosen identifier;
   - set `contribution_licensing_confirmed` only after contribution licensing
     is documented and accepted by the owner;
   - set `security_contact_confirmed` only after GitHub private vulnerability
     reporting is enabled or a private security contact path exists;
   - keep `dist_release_policy` explicit.
4. Update `CONTRIBUTING.md` if contribution licensing terms need clearer owner
   confirmation.
5. Update `SECURITY.md` if a private vulnerability reporting path needs to be
   documented.
6. Regenerate scorecards and public benchmark summaries.

Until all of these are complete, the correct public status is structurally close
to open-source-ready, but not publishable as open source.
