# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Documentation verification tests for CAMT.054 loader."""

from decimal import Decimal

from bankstatementparser_loader_camt054 import load_camt054, summarize_camt054


def test_readme_examples() -> None:
    """Verify README snippets."""
    sample = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.02">
  <BkToCstmrDbtCdtNtfctn>
    <GrpHdr><MsgId>MSG-2026-001</MsgId></GrpHdr>
    <Ntfctn>
      <Id>NTF-01</Id>
      <Acct><Id><IBAN>FR7630006000011234567890189</IBAN></Id><Ccy>EUR</Ccy></Acct>
      <Ntry>
        <Amt Ccy="EUR">150.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-01-15</Dt></BookgDt>
      </Ntry>
    </Ntfctn>
  </BkToCstmrDbtCdtNtfctn>
</Document>"""
    txns = load_camt054(sample)
    assert len(txns) == 1
    assert txns[0].amount == Decimal("150.00")

    summary = summarize_camt054(sample)
    assert summary.message_id == "MSG-2026-001"
    assert summary.total_entries == 1
