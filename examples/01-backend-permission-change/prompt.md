# Prompt

Add a backend endpoint that lets an account admin download invoices for their organization. The endpoint should reject users from other organizations and preserve the existing API response style. Include an independent security review of tenant isolation: a caller-controlled invoice identifier must never expose another organization's invoice.
