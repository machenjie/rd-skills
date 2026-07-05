# Permission Boundary Modeling Checklist

- Identify subjects: users, roles, support, admins, service accounts, jobs, and external systems.
- Identify resources and object-level ownership.
- Identify actions: read, create, update, delete, export, approve, cancel, impersonate, and administer.
- Identify conditions: tenant, owner, lifecycle state, policy, time, environment, and sensitivity.
- Define allow and deny decisions.
- Define backend enforcement point for every action.
- Define denial behavior without restricted-data leakage.
- Define audit requirements for access and mutation.
- Check bulk, async, import, admin, and support paths.
- Map permissions to tests.
