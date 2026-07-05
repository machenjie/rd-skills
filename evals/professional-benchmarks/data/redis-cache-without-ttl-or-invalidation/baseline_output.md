Add Redis around entitlement lookup with key `entitlement:{id}`.

The default Redis memory policy should be fine and we can clear Redis manually if values look wrong. I skipped metrics because this is just a performance cache.

No tests are needed beyond existing entitlement tests.
