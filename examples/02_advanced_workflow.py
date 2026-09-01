# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Advanced batch processing example for bankstatementparser-loader-camt054."""

from decimal import Decimal

from bankstatementparser_loader_camt054 import load_camt054

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.02">
  <BkToCstmrDbtCdtNtfctn>
    <GrpHdr><MsgId>MSG-2026-001</MsgId></GrpHdr>
    <Ntfctn>
      <Id>NTF-01</Id>
      <Acct><Id><IBAN>FR7630006000011234567890189</IBAN></Id><Ccy>EUR</Ccy></Acct>
      <Ntry>
        <Amt Ccy="EUR">250.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-01-15</Dt></BookgDt>
        <NtryDtls><TxDtls><Refs><EndToEndId>E2E-001</EndToEndId></Refs><RmtInf><Ustrd>Client Invoice 101</Ustrd></RmtInf></TxDtls></NtryDtls>
      </Ntry>
    </Ntfctn>
  </BkToCstmrDbtCdtNtfctn>
</Document>"""


def main() -> None:
    print("Batch processing 100 iterations...")
    total_volume = Decimal("0")
    for _ in range(100):
        txns = load_camt054(SAMPLE)
        for t in txns:
            total_volume += abs(t.amount)
    print(
        f"Processed 100 batch statements. Total absolute volume: {total_volume}"
    )


if __name__ == "__main__":
    main()
