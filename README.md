# VeriPulse — Concordium Trusted AI Agent (CIS-8004, x402 & EU AI Act Art. 12)

Submission for **Concordium Trusted Agents Hackathon** on Encode Club (`3,000,000 CCD` Prize Pool).

## Overview
**VeriPulse** adds verified human accountability, zero-knowledge compliance, and sponsored micropayment settlement to autonomous AI agents on **Concordium Testnet**:
1. **Concordium Verify & Access (`verify_zk_identity`)**: Verifies `age >= 18`, jurisdiction eligibility, and sanctions screening in zero knowledge without exposing raw PII.
2. **CIS-8004 / ERC-8004 Agent Registry (`CIS8004AgentCard`)**: Publishes the `Verified by Concordium` badge, owner & sponsor accounts, and supported A2A/MCP protocols (`registry_contract_index: 9412`).
3. **x402 Sponsored Micropayments (`execute_x402_sponsored_task`)**: Settles `250,000 microCCD` (`0.25 CCD`) per agent task while delegating transaction energy (`480 NRG`) to a Concordium Sponsor Account, linking directly to `https://testnet.ccdexplorer.io/transaction/<hash>`.
4. **EU AI Act Article 12 Tamper-Evident Audit Trail (`verify_audit_chain_integrity`)**: Records every identity check, rejection, and x402 execution in a SHA-256 hash chain.

## Run & Test Locally
```bash
python -m unittest discover -s tests -v
python backend/server.py
# Open http://127.0.0.1:8093
```
