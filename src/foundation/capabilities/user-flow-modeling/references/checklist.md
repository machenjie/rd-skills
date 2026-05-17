# User Flow Modeling Checklist

- Name the actor and goal.
- List all entry points, including deep links, notifications, search, and admin links.
- Define starting state and required preconditions.
- Model main path to success.
- Define success exits and where the user lands next.
- Define validation, dependency, timeout, and system failure exits.
- Define cancellation behavior and whether work is reversed, stopped, or completed later.
- Define retry behavior and idempotency requirements.
- Define back navigation, browser refresh, and preserved state.
- Define permission branches without restricted-data leakage.
