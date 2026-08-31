# ISO 20022 CAMT.054 Notification Loader for Bank Statement Parser

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0_OR_MIT-blue.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/sebastienrousseau/bankstatementparser-loader-camt054)

An enterprise-grade ISO 20022 `camt.054.001.xx` (Bank-to-Customer Debit/Credit Notification) XML loader plugin for [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser).

---

## Features

- **ISO 20022 CAMT.054 Support**: Complete ingest of `camt.054.001.02` through `camt.054.001.10` notification messages.
- **Entry & Transaction Level Detail**: Intelligently extracts both `<Ntry>` high-level entries and nested `<TxDtls>` individual transaction details.
- **Counterparty & Reference Extraction**: Automatic extraction of debtor/creditor names, IBANs, EndToEnd IDs, Bank References, and Remittance Information (`RmtInf/Ustrd` and `Strd`).
- **Defused XML Security**: Built on `defusedxml` to protect against XML External Entity (XXE) and quadratic blowup attacks.
- **Seamless Plugin Integration**: Dynamically registers under `bankstatementparser.loaders` entry points (`camt054`, `camt_054`).

---

## Installation

```bash
pip install bankstatementparser-loader-camt054
```

---

## Quickstart

```python
from bankstatementparser_loader_camt054 import load_camt054_file, summarize_camt054

# 1. Parse notifications into standard Transaction models
transactions = load_camt054_file("notification.xml")
for tx in transactions:
    print(f"{tx.booking_date} | {tx.description} | {tx.amount} {tx.currency}")

# 2. Get notification message summary
summary = summarize_camt054(open("notification.xml").read())
print(f"Message ID: {summary.message_id}")
print(f"Total Credit: {summary.total_credit} | Total Debit: {summary.total_debit}")
```

---

## License

Dual-licensed under Apache 2.0 and MIT.
