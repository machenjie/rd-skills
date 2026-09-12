from __future__ import annotations

import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD = runpy.run_path(str(
    ROOT / "examples/01-backend-permission-change/invoice_download.py"
))["download_invoice"]


class InvoiceDownloadExampleTests(unittest.TestCase):
    def setUp(self):
        self.admin = {"organization_id": "acme", "is_admin": True}
        self.invoices = (
            {"id": "shared", "organization_id": "other", "content": "Other secret"},
            {"id": "shared", "organization_id": "acme", "content": "Acme invoice"},
            {"id": "other-only", "organization_id": "other", "content": "Other secret"},
        )

    def test_admin_receives_own_invoice_even_when_ids_collide(self):
        self.assertEqual(
            (200, {"invoice_id": "shared", "content": "Acme invoice"}),
            DOWNLOAD(self.admin, "shared", self.invoices),
        )

    def test_cross_organization_and_missing_id_have_same_response(self):
        for invoice_id in ("other-only", "missing"):
            with self.subTest(invoice_id=invoice_id):
                self.assertEqual(
                    (404, {"error": "invoice_not_found"}),
                    DOWNLOAD(self.admin, invoice_id, self.invoices),
                )

    def test_non_admin_is_denied(self):
        principal = {"organization_id": "acme", "is_admin": False}
        self.assertEqual((403, {"error": "forbidden"}),
                         DOWNLOAD(principal, "shared", self.invoices))

    def test_unauthenticated_is_denied(self):
        self.assertEqual((401, {"error": "unauthenticated"}),
                         DOWNLOAD(None, "shared", self.invoices))

    def test_invalid_id_preserves_error_shape(self):
        for invoice_id in (None, "", "  ", 7):
            with self.subTest(invoice_id=invoice_id):
                self.assertEqual((400, {"error": "invalid_invoice_id"}),
                                 DOWNLOAD(self.admin, invoice_id, self.invoices))

    def test_empty_repository_is_not_found(self):
        self.assertEqual((404, {"error": "invoice_not_found"}),
                         DOWNLOAD(self.admin, "shared", ()))


if __name__ == "__main__":
    unittest.main()
