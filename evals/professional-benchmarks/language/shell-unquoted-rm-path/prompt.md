Review this shell script:

`cleanup.sh` runs `rm -rf $TARGET/*`, accepts `$TARGET` from the environment,
passes `--password $SECRET` to a subprocess, and has no `trap`, no dry-run, and
no shellcheck or bats evidence.
