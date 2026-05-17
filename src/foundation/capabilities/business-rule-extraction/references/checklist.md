# Business Rule Extraction Checklist

- Identify eligibility, limit, calculation, lifecycle, authorization-adjacent, and compliance rules.
- Separate domain rules from UI convenience, request parsing, and storage mechanics.
- Name the rule owner and authoritative source.
- Define enforcement layer and all entry points that must obey the rule.
- Identify invariants that must always hold.
- Record exceptions, precedence, and effective dates when relevant.
- Identify audit, reporting, and historical meaning.
- Check batch jobs, imports, admin tools, scripts, and migrations.
- Prevent duplicate rule implementation across layers.
- Define tests or review evidence for each rule.
