# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Only a plain ISO 20022 decimal is an amount.

An ISO 20022 amount is unsigned ASCII digits with an optional decimal
part; the sign comes from ``CdtDbtInd``. ``Decimal`` accepts far more:
``NaN`` and ``Infinity`` (which escaped ``load_camt054`` as a pydantic
``ValidationError`` and ``summarize_camt054`` as
``decimal.InvalidOperation`` or an infinite total), exponents, ``_``
separators, a sign, and other scripts' digits. The loader already
skips an entry whose amount does not parse and ignores a detail amount
that does not; these now fall under that rule too.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from bankstatementparser_loader_camt054 import load_camt054, summarize_camt054
from bankstatementparser_loader_camt054.loader import _parse_amount

_ENTRY = """<Document><BkToCstmrDbtCdtNtfctn><Ntfctn>
<Ntry><Amt Ccy="EUR">{entry}</Amt><CdtDbtInd>CRDT</CdtDbtInd>{details}</Ntry>
<Ntry><Amt Ccy="EUR">7.00</Amt><CdtDbtInd>DBIT</CdtDbtInd></Ntry>
</Ntfctn></BkToCstmrDbtCdtNtfctn></Document>"""

_DETAIL = (
    '<NtryDtls><TxDtls><AmtDtls><TxAmt><Amt Ccy="USD">{detail}</Amt>'
    "</TxAmt></AmtDtls></TxDtls></NtryDtls>"
)

_BAD = [
    "NaN",
    "sNaN",
    "Infinity",
    "-Infinity",
    "1e5",
    "1_000",
    "-5",
    "+5",
    "٣",
    "12.5.3",
    "1.",
    ".5",
]


@pytest.mark.parametrize("raw", _BAD)
def test_malformed_entry_amount_skips_the_entry(raw: str) -> None:
    """The entry is skipped; the next one still loads and sums."""
    xml = _ENTRY.format(entry=raw, details="")
    assert [t.amount for t in load_camt054(xml)] == [Decimal("-7.00")]
    summary = summarize_camt054(xml)
    assert (summary.total_credit, summary.total_debit) == (
        Decimal("0.00"),
        Decimal("7.00"),
    )


@pytest.mark.parametrize("raw", _BAD)
def test_malformed_detail_amount_keeps_the_entry_amount(raw: str) -> None:
    """A detail amount that is not a decimal does not override."""
    xml = _ENTRY.format(entry="10.00", details=_DETAIL.format(detail=raw))
    first = load_camt054(xml)[0]
    assert (first.amount, first.currency) == (Decimal("10.00"), "EUR")


@pytest.mark.parametrize(
    ("raw", "value"),
    [("10", "10"), (" 10.50 ", "10.50"), ("0.00001", "0.00001")],
)
def test_plain_decimals_parse(raw: str, value: str) -> None:
    """Unsigned ASCII digits with an optional fraction are amounts."""
    assert _parse_amount(raw) == Decimal(value)


@pytest.mark.parametrize("raw", _BAD)
def test_everything_else_is_not_an_amount(raw: str) -> None:
    """The helper refuses what Decimal would have accepted or raised."""
    assert _parse_amount(raw) is None
