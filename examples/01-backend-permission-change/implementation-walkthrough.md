# Invoice Download Implementation Walkthrough

This fictional in-memory example teaches one authorization decision. It is not a
framework template, an HTTP endpoint, or a benchmark answer. The expected route
still describes how work on a real repository would be assigned.

## Request And Existing Contract

An authenticated account admin may download an invoice only from their own
organization. Here `principal` comes from trusted server authentication, never
request JSON. Invoice IDs may overlap across organizations. The existing response
shape is `(status, body)`: unauthenticated callers receive 401, non-admins 403,
invalid IDs 400, and missing or inaccessible invoices the same 404 error body.
An authorized response contains only the invoice ID and content.

## Fault And Cause

The initial implementation checked admin status but then used this lookup:

```python
invoice = next((item for item in invoices if item["id"] == invoice_id), None)
```

An admin could request another organization's ID and receive its content. If IDs
collided, list order determined whose content was returned. Admin role alone did
not establish object ownership. In a real repository, inspect sibling download
and export lookups for the same unscoped access before calling the repair local.

## Placement And Choice

Keep the authorization decision at the existing invoice download owner. Scope
selection by both the authenticated organization and requested ID before returning
content. Reject trusting an organization supplied with the request: callers can
change it. Reject role-only checks and global lookup followed by an existence
message: both can reveal another organization's data or existence.

The toy function owns selection and response shaping because it has no repository
layer. In a real service, use its existing scoped query and policy owner; do not
create a new repository interface to copy this example. A signed-storage URL, if
used, must be issued only after that authorization decision.

## Final Implementation

Read [invoice_download.py](invoice_download.py). Its change is the organization
predicate in the existing lookup; error and success bodies remain unchanged.
The single function uses only Python's standard library and introduces no
persistence, server, dependency, or authorization framework.

## Behavioral Verification

From the repository root, run:

```bash
python3 -m unittest discover -s tests/scripts -p test_invoice_download_example.py
```

The [tests](../../tests/scripts/test_invoice_download_example.py) execute the
function. With the vulnerable lookup, the cross-organization and colliding-ID
cases fail because foreign content is returned. With the scoped lookup, an admin
gets their own content and foreign or missing IDs return the same 404. Other
cases cover non-admins, unauthenticated callers, invalid IDs and an empty store.
To observe RED, temporarily substitute the faulty line above in a disposable copy;
restore the scoped lookup and run the same command for GREEN.

This proves only the toy function's response behavior. It does not establish
authentication correctness, HTTP integration, database isolation under concurrent
changes, storage URL policy, response timing equivalence, or real-host execution.
