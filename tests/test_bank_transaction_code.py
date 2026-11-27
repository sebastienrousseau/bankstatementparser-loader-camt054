# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""The entry's bank transaction code reaches ``category``.

ISO 20022 nests the code: ``BkTxCd/Prtry/Cd`` for the bank's own code,
``BkTxCd/Domn/Cd`` for the standard domain. The loader looked only for
text directly in ``BkTxCd`` or ``Prtry``, which a schema-valid file
never has, so ``category`` was ``None`` for every real notification.
"""

from __future__ import annotations

import pytest

from bankstatementparser_loader_camt054 import load_camt054

_DOC = """<Document><BkToCstmrDbtCdtNtfctn><Ntfctn><Ntry>
<Amt Ccy="EUR">5.00</Amt><CdtDbtInd>CRDT</CdtDbtInd>{code}
</Ntry></Ntfctn></BkToCstmrDbtCdtNtfctn></Document>"""


@pytest.mark.parametrize(
    ("code", "category"),
    [
        ("<BkTxCd><Prtry><Cd>SEPA-CT</Cd></Prtry></BkTxCd>", "SEPA-CT"),
        (
            "<BkTxCd><Domn><Cd>PMNT</Cd><Fmly><Cd>RCDT</Cd>"
            "<SubFmlyCd>ESCT</SubFmlyCd></Fmly></Domn></BkTxCd>",
            "PMNT",
        ),
        (
            "<BkTxCd><Domn><Cd>PMNT</Cd></Domn>"
            "<Prtry><Cd>NTRF</Cd><Issr>SWIFT</Issr></Prtry></BkTxCd>",
            "NTRF",
        ),
        ("<BkTxCd>FLAT</BkTxCd>", "FLAT"),
        ("<BkTxCd><Prtry>FLATPRTRY</Prtry></BkTxCd>", "FLATPRTRY"),
    ],
)
def test_category_carries_the_code(code: str, category: str) -> None:
    """Proprietary first, then the domain, then the flat forms."""
    (tx,) = load_camt054(_DOC.format(code=code))
    assert tx.category == f"camt054:{category}"
    assert tx.description == category


@pytest.mark.parametrize(
    "code", ["", "<BkTxCd/>", "<BkTxCd><Domn><Fmly/></Domn></BkTxCd>"]
)
def test_no_code_no_category(code: str) -> None:
    """An entry without a code has no category or description."""
    (tx,) = load_camt054(_DOC.format(code=code))
    assert tx.category is None
    assert tx.description is None
