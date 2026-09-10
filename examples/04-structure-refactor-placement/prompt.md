# Prompt

Refactor duplicated order total calculation in checkout, invoice generation, and the admin refund screen. Checkout rounds each line, invoices round the final total, and refunds use stored totals. Before editing, analyze whether these are the same business rule and where any shared calculation belongs; preserve intentional differences and report any rule that current source and tests cannot settle.
