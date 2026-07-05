# Module Boundary Design Checklist

- Name each module by business capability and responsibility.
- Define public interface and private internals.
- Define allowed and forbidden dependency directions.
- Check for circular dependencies and shared mutable state.
- Identify owner or review authority for each module.
- Prevent internal repositories, tables, or DTOs from becoming module contracts.
- Locate shared code and confirm it is policy-free or clearly owned.
- Define test boundaries and contract verification.
- Record migration steps for moved or split code.
