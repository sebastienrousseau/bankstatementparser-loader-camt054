# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""High-load concurrency and stress testing for CAMT.054 loader."""

import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from bankstatementparser_loader_camt054 import load_camt054

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
        <NtryDtls><TxDtls><Refs><EndToEndId>E2E-1</EndToEndId></Refs><RmtInf><Ustrd>Payment 1</Ustrd></RmtInf></TxDtls></NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">50.00</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt><Dt>2026-01-16</Dt></BookgDt>
        <NtryDtls><TxDtls><Refs><EndToEndId>E2E-2</EndToEndId></Refs><RmtInf><Ustrd>Fee</Ustrd></RmtInf></TxDtls></NtryDtls>
      </Ntry>
    </Ntfctn>
  </BkToCstmrDbtCdtNtfctn>
</Document>"""


def test_camt054_concurrency_and_throughput() -> None:
    """Verify concurrent parsing of CAMT.054 feeds."""
    iterations = 1000
    workers = 8

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(load_camt054, SAMPLE_XML)
            for _ in range(iterations)
        ]
        results = [f.result() for f in futures]
    elapsed = time.perf_counter() - start

    assert len(results) == iterations
    for txns in results:
        assert len(txns) == 2
        assert txns[0].amount == Decimal("150.00")
        assert txns[1].amount == Decimal("-50.00")
    assert elapsed < 10.0
