# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Coverage-guided Atheris fuzz target for the CAMT.054 loader.

``load_camt054`` and ``summarize_camt054`` are the package's entry
points for untrusted bytes. Their documented failures are the XML
parser's: ``xml.etree.ElementTree.ParseError`` for text that is not
well-formed XML, and defusedxml's ``DefusedXmlException`` for a DTD,
an entity or an external reference. Anything the loader does not model
inside a well-formed document is skipped. Any other exception escapes
the target and libFuzzer records it as a crash.

Every transaction that loads must also be well formed: a finite
amount, ``source == "camt054"`` and, when it has a category, a
``camt054:<code>`` one; and the summary of the same bytes must count
the same entries and net to the same total.

Run (Linux x86_64, Python 3.12+, ``poetry install --with fuzz``)::

    python fuzz/fuzz_load_camt054.py fuzz/corpus -max_total_time=60
"""

from __future__ import annotations

import sys
from decimal import Decimal
from xml.etree.ElementTree import ParseError  # nosec B405

import atheris
from defusedxml import DefusedXmlException

with atheris.instrument_imports():
    from bankstatementparser_loader_camt054 import (
        load_camt054,
        summarize_camt054,
    )


def test_one_input(data: bytes) -> None:
    """Load and summarise one fuzz input as CAMT.054 bytes."""
    try:
        transactions = load_camt054(data)
    except (ParseError, DefusedXmlException):
        return
    net = Decimal(0)
    for txn in transactions:
        if not txn.amount.is_finite():
            raise AssertionError(f"non-finite amount {txn.amount!r}")
        category = txn.category or "camt054:"
        if txn.source != "camt054" or not category.startswith("camt054:"):
            raise AssertionError(f"mislabelled transaction {txn!r}")
        net += txn.amount
    summary = summarize_camt054(data)
    if summary.entry_count != len(transactions):
        raise AssertionError("summary and load disagree on the count")
    if summary.total_credit - summary.total_debit != net:
        raise AssertionError("summary and load disagree on the total")


def main() -> None:
    """Hand the target to libFuzzer with the command-line options."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
