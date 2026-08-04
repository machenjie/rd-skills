# Migration Review

Take the snapshot first, start CDC from wall-clock time after the snapshot, and allow both jobs to upsert by primary key. We can let backfill and live processing write without precedence because later writes should win. Declare success from row-count parity alone and switch consumers once counts match.
