#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
"""What a CAMT.054 notification costs to load, as it grows.

A camt.054 is a bank's debit/credit notification: one XML document,
one ``Ntry`` per booking, and inside a batched booking one ``TxDtls``
per underlying payment. Two axes move in practice, so both are
measured:

* **Entries per notification** (``Ntry`` elements under one
  ``Ntfctn``): an end-of-day file for a busy account.
* **Transactions per entry** (``TxDtls`` under one ``Ntry``): a batch
  booking, such as a collection of Direct Debits credited as one sum.

Read ``us/txn``. Flat means linear. Climbing means something rescans
what it has already read: every lookup in the loader walks an
element's subtree, so a large batch is where that would show.

``summarize_camt054`` is measured beside ``load_camt054``: it parses
the same document but builds no ``Transaction`` objects.

Run::

    python benches/bench_load_camt054.py
    python benches/bench_load_camt054.py --json
    python benches/bench_load_camt054.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped running against the
current API fails the build instead of rotting into a file that reads
as verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bankstatementparser_loader_camt054 import (  # noqa: E402
    load_camt054,
    summarize_camt054,
)

HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.08">'
    "<BkToCstmrDbtCdtNtfctn><GrpHdr><MsgId>BENCH</MsgId>"
    "<CreDtTm>2026-01-15T09:30:00Z</CreDtTm></GrpHdr><Ntfctn>"
    "<Id>N1</Id><Acct><Id><IBAN>FR7630006000011234567890189</IBAN></Id>"
    "</Acct>"
)
TAIL = "</Ntfctn></BkToCstmrDbtCdtNtfctn></Document>"


def tx_details(e: int, i: int) -> str:
    """One ``TxDtls`` with its own amount, party and remittance text."""
    return (
        f"<TxDtls><Refs><EndToEndId>E2E-{e}-{i}</EndToEndId></Refs>"
        f'<AmtDtls><TxAmt><Amt Ccy="EUR">{i + 1}.00</Amt></TxAmt></AmtDtls>'
        f"<RltdPties><Dbtr><Nm>Customer {i}</Nm></Dbtr></RltdPties>"
        f"<RmtInf><Ustrd>Invoice {e}-{i}</Ustrd></RmtInf></TxDtls>"
    )


def entry(e: int, details: int) -> str:
    """One ``Ntry`` booking ``details`` transactions."""
    total = sum(i + 1 for i in range(details))
    return (
        f'<Ntry><Amt Ccy="EUR">{total}.00</Amt>'
        f"<CdtDbtInd>{'CRDT' if e % 2 == 0 else 'DBIT'}</CdtDbtInd>"
        "<BookgDt><Dt>2026-01-15</Dt></BookgDt>"
        f"<AcctSvcrRef>REF-{e}</AcctSvcrRef>"
        "<BkTxCd><Prtry><Cd>SEPA</Cd></Prtry></BkTxCd><NtryDtls>"
        + "".join(tx_details(e, i) for i in range(details))
        + "</NtryDtls></Ntry>"
    )


def build(entries: int, details: int) -> str:
    """A notification of ``entries`` entries of ``details`` each."""
    return HEAD + "".join(entry(e, details) for e in range(entries)) + TAIL


def _best(call: Callable[[], object], repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine happens to be doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def measure(entries: int, details: int, repeats: int) -> dict[str, Any]:
    """Time ``load_camt054`` and ``summarize_camt054`` on one shape."""
    text = build(entries, details)
    load = _best(lambda: load_camt054(text), repeats)
    summary = _best(lambda: summarize_camt054(text), repeats)
    transactions = len(load_camt054(text))
    expected = entries * details
    if transactions != expected or (
        summarize_camt054(text).entry_count != expected
    ):
        raise SystemExit(f"expected {expected} rows, read {transactions}")
    return {
        "entries": entries,
        "details_each": details,
        "transactions": transactions,
        "bytes": len(text),
        "load_ms": load * 1e3,
        "summary_ms": summary * 1e3,
        "us_per_txn": load * 1e6 / transactions,
        "summary_over_load": summary / load,
    }


def run(quick: bool) -> list[dict[str, Any]]:
    """Measure every shape; ``quick`` keeps to the small ones."""
    if quick:
        shapes, repeats = [(10, 1), (100, 1)], 3
    else:
        shapes = [(10, 1), (100, 1), (1_000, 1), (10_000, 1), (100, 100)]
        repeats = 7
    return [measure(e, d, repeats) for e, d in shapes]


def render(rows: list[dict[str, Any]]) -> None:
    """Print the table and what it means."""
    print(
        f"{'entries':>9}{'txns each':>11}{'total':>8}{'KiB':>9}"
        f"{'load ms':>10}{'summary ms':>12}{'us/txn':>9}"
    )
    for row in rows:
        print(
            f"{row['entries']:>9}{row['details_each']:>11}"
            f"{row['transactions']:>8}{row['bytes'] / 1024:>9.1f}"
            f"{row['load_ms']:>10.2f}{row['summary_ms']:>12.2f}"
            f"{row['us_per_txn']:>9.2f}"
        )
    drift = rows[-1]["us_per_txn"] / rows[0]["us_per_txn"]
    print(
        f"\n  us/txn for the last shape is {drift:.2f}x the first. Flat "
        f"is linear; climbing means something rescans what it has "
        f"already read."
    )
    worst = max(r["summary_over_load"] for r in rows)
    print(
        f"\n  summarize_camt054 costs up to {worst:.2f}x load_camt054: both "
        f"parse the whole document, and the summary saves only the "
        f"Transaction objects."
    )


def main() -> int:
    """Parse the options, run, and print a table or JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    rows = run(quick=args.quick)
    if args.json:
        json.dump(rows, sys.stdout, indent=1)
        print()
    else:
        render(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
