"""Unit and integration tests for VeriPulse Concordium Trusted Agent."""

from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.concordium_agent import VeriPulseConcordiumEngine
from backend.server import create_server


class TestVeriPulseConcordium(unittest.TestCase):
    """Verifies Concordium ZK identity gates, x402 sponsored settlement, and Article 12 hash chain."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.srv = create_server(port=0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.srv.shutdown()
        cls.srv.server_close()

    def test_unverified_caller_blocked_from_x402_skill(self) -> None:
        eng = VeriPulseConcordiumEngine()
        with self.assertRaises(ValueError):
            eng.execute_x402_sponsored_task("unverified-cred", "portfolio-audit", "test")

        # Failed predicate (under 18 or sanctioned) must also reject and log.
        with self.assertRaises(ValueError):
            eng.verify_zk_identity("sanctioned-cred-01", age_over_18=True, sanctions_passed=False)
        self.assertEqual(len(eng.audit_chain), 1)
        self.assertEqual(eng.audit_chain[0].event_type, "ZK_IDENTITY_REJECTED")
        self.assertTrue(eng.verify_audit_chain_integrity())

    def test_zk_verify_and_x402_sponsored_execution_chain(self) -> None:
        eng = VeriPulseConcordiumEngine()
        stmt = eng.verify_zk_identity("ccd-cred-alpha99")
        self.assertTrue(stmt.proof_commitment_hex.startswith("0x"))

        res = eng.execute_x402_sponsored_task(
            credential_id="ccd-cred-alpha99",
            service_skill="treasury-risk-audit",
            task_input="Audit 50,000 CCD liquidity pool",
        )
        self.assertEqual(res["settlement"]["status"], "SETTLED_SPONSORED")
        self.assertEqual(res["settlement"]["amount_micro_ccd"], 250_000)
        self.assertIn("testnet.ccdexplorer.io/transaction/", res["settlement"]["ccdexplorer_url"])
        self.assertTrue(eng.verify_audit_chain_integrity())

    def test_http_api_end_to_end(self) -> None:
        v_req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/verify_id",
            data=json.dumps({"credentialId": "ccd-cred-http01"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(v_req, timeout=5) as r1:
            d1 = json.loads(r1.read().decode("utf-8"))
        self.assertEqual(d1["state"]["verifiedCount"], 1)

        x_req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/execute_x402",
            data=json.dumps(
                {
                    "credentialId": "ccd-cred-http01",
                    "serviceSkill": "cis8004-counterparty-check",
                    "taskInput": "Verify merchant agent #9412",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(x_req, timeout=5) as r2:
            d2 = json.loads(r2.read().decode("utf-8"))
        self.assertTrue(d2["state"]["auditIntegrityValid"])
        self.assertEqual(len(d2["state"]["settlements"]), 1)


if __name__ == "__main__":
    unittest.main()
