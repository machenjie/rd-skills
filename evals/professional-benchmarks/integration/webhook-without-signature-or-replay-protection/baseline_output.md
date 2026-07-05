Parse the JSON webhook payload and update the subscription state based on the event type.

The provider retries failed events, so we can assume delivery eventually succeeds. Signature checks can be added later if needed.

No replay table is required for the first version.
