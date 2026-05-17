# Routing Navigation Design Checklist

- Create a route table with path, owner, parameters, required data, and title or label.
- Define unauthenticated, unauthorized, unavailable, stale-link, and not-found outcomes.
- Confirm frontend guards do not replace backend authorization.
- Define redirect source, target, reason, loop prevention, and return destination behavior.
- Validate route parameters and canonical route shape.
- Define direct deep-link loading and recovery behavior.
- Define browser back, refresh, and external-link behavior.
- Include safe landing pages for removed or inaccessible resources.
- Check that route errors do not leak sensitive resource details.
- Add route-level tests for permission branches, 404, stale links, and recovery.
