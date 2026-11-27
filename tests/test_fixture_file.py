# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Golden test for ``tests/fixtures/notification.xml``.

The fixture is a camt.054.001.08 notification with one account: a
credit entry batching two transfers (each ``TxDtls`` with its own
amount) and a Direct Debit entry. The README demo and the fuzz seeds
use it; this pins what the loader reads from it.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from bankstatementparser_loader_camt054 import (
    Camt054StatementParser,
    load_camt054_file,
    summarize_camt054,
)

FIXTURE = Path(__file__).parent / "fixtures" / "notification.xml"
IBAN = "FR7630006000011234567890189"


def test_transactions() -> None:
    """One transaction per TxDtls, signed by the entry's CdtDbtInd."""
    rows = [
        (
            t.booking_date,
            t.value_date,
            t.amount,
            t.category,
            t.reference,
            t.description,
        )
        for t in load_camt054_file(FIXTURE)
    ]
    credit = (date(2026, 1, 15), date(2026, 1, 16))
    assert rows == [
        (
            *credit,
            Decimal("1000.00"),
            "camt054:SEPA-CT",
            "INV-2026-101",
            "SEPA-CT - Invoice 101",
        ),
        (
            *credit,
            Decimal("250.00"),
            "camt054:SEPA-CT",
            "INV-2026-102",
            "SEPA-CT - Invoice 102",
        ),
        (
            date(2026, 1, 15),
            date(2026, 1, 15),
            Decimal("-89.90"),
            "camt054:SEPA-DD",
            "MANDATE-77",
            "SEPA-DD - January electricity",
        ),
    ]
    assert {t.account_id for t in load_camt054_file(FIXTURE)} == {IBAN}


def test_summary() -> None:
    """The summary carries the group header and the totals."""
    summary = summarize_camt054(FIXTURE.read_bytes())
    assert summary.message_id == "NTF-2026-0115-001"
    assert summary.creation_date == datetime(
        2026, 1, 15, 9, 30, tzinfo=timezone.utc
    )
    assert (summary.account_id, summary.currency) == (IBAN, "EUR")
    assert (summary.notification_count, summary.entry_count) == (1, 3)
    assert summary.total_credit == Decimal("1250.00")
    assert summary.total_debit == Decimal("89.90")


def test_parser_plugin() -> None:
    """The core's plugin interface reads the same file."""
    parser = Camt054StatementParser(str(FIXTURE))
    assert list(parser.parse()["amount"]) == [1000.0, 250.0, -89.9]
    assert parser.get_summary()["entry_count"] == 3
