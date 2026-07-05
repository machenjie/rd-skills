The timeout is likely the cause. Add a retry guard and rerun the payment tests.

I would propose a patch before mapping the violated invariant and treat timeout
as root cause without proof.
