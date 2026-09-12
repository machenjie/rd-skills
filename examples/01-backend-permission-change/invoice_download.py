"""Fictional invoice download boundary; no HTTP server or authentication adapter."""


def download_invoice(principal, invoice_id, invoices):
    """Principal is trusted server-authenticated context, never request JSON."""
    if principal is None:
        return 401, {"error": "unauthenticated"}
    if not principal["is_admin"]:
        return 403, {"error": "forbidden"}
    if not isinstance(invoice_id, str) or not invoice_id.strip():
        return 400, {"error": "invalid_invoice_id"}
    invoice = next((item for item in invoices
                    if item["id"] == invoice_id
                    and item["organization_id"] == principal["organization_id"]), None)
    if invoice is None:
        return 404, {"error": "invoice_not_found"}
    return 200, {"invoice_id": invoice["id"], "content": invoice["content"]}
