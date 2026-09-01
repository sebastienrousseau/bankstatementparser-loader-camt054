<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img
    src="https://cloudcdn.pro/bankstatementparser/v1/logos/bankstatementparser.svg"
    alt="bankstatementparser-loader-camt054 logo"
    width="120"
    height="120"
  />
</p>

<h1 align="center">bankstatementparser-loader-camt054</h1>

<p align="center">
  <b>ISO 20022 CAMT.054 Bank-to-Customer Debit/Credit Notification loader plugin for bankstatementparser.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/bankstatementparser-loader-camt054/"><img src="https://img.shields.io/pypi/v/bankstatementparser-loader-camt054?style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/bankstatementparser-loader-camt054/"><img src="https://img.shields.io/pypi/pyversions/bankstatementparser-loader-camt054.svg?style=for-the-badge" alt="Python versions" /></a>
  <a href="https://pypi.org/project/bankstatementparser-loader-camt054/"><img src="https://img.shields.io/pypi/dm/bankstatementparser-loader-camt054.svg?style=for-the-badge" alt="PyPI downloads" /></a>
  <a href="https://github.com/sebastienrousseau/bankstatementparser-loader-camt054/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/bankstatementparser-loader-camt054/ci.yml?branch=main&label=Tests&style=for-the-badge" alt="Tests" /></a>
  <a href="#license"><img src="https://img.shields.io/pypi/l/bankstatementparser-loader-camt054?style=for-the-badge" alt="License" /></a>
</p>

---

## Contents

- [What is bankstatementparser-loader-camt054?](#what-is-bankstatementparser-loader-camt054) — the problem it solves
- [Install](#install) — PyPI, virtualenv
- [Quick start](#quick-start) — ingest notifications in three lines
- [Public API](#public-api) — `load_camt054`, `load_camt054_file`, `summarize_camt054`
- [Supported ISO 20022 schemas](#supported-iso-20022-schemas) — XML schema namespaces
- [Amount and sign convention](#amount-and-sign-convention) — Credit / Debit indicators
- [Development](#development) — quality gates, tests
- [Ecosystem](#ecosystem) — modular package suite
- [Contributing](#contributing)
- [License](#license)

---

## What is bankstatementparser-loader-camt054?

**CAMT.054** (Bank-to-Customer Debit/Credit Notification) is the ISO 20022 XML standard used by global banks and corporate treasuries for real-time transaction reporting and intraday movement feeds.

**bankstatementparser-loader-camt054** provides full schema support for ingesting CAMT.054 XML feeds into unified `bankstatementparser` `Transaction` objects and `pandas.DataFrame` tables.

| Concern | How this loader handles it |
| :--- | :--- |
| **Schema Versions** | Supports `camt.054.001.02`, `camt.054.001.04`, `camt.054.001.08`, and generic variants |
| **Stream Extraction** | Parses multi-notification files (`<Ntfctn>`), entry batches (`<Ntry>`), and sub-item transaction details (`<TxDtls>`) |
| **References** | Extracts EndToEndId, InstructionId, AccountServicerReference, MandateId, and unstructured remittance |
| **Account Resolution** | Automatically identifies IBAN, BBAN, or Proprietary Account Identifiers |
| **Amounts** | Exact `Decimal` amounts signed according to `<CdtDbtInd>` (`CRDT` vs `DBIT`) |

---

## Install

| Channel | Command | Notes |
| :--- | :--- | :--- |
| PyPI | `pip install bankstatementparser-loader-camt054` | Pulls in `bankstatementparser >= 0.0.19` |
| Source | `git clone https://github.com/sebastienrousseau/bankstatementparser-loader-camt054 && cd bankstatementparser-loader-camt054 && poetry install` | For local development |

Requires Python 3.10 or later. Compatible with macOS, Linux, and Windows.

<details>
<summary>Using an isolated virtual environment (recommended)</summary>

```sh
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
python -m pip install -U bankstatementparser-loader-camt054
```

</details>

---


## Quick start

```python
from bankstatementparser_loader_camt054 import load_camt054_file, summarize_camt054

# Ingest notification XML stream into Transaction models
transactions = load_camt054_file("notification.xml")
for tx in transactions:
    print(f"{tx.booking_date} | {tx.description} | {tx.amount} {tx.currency}")

# Extract batch metadata and notification summary
summary = summarize_camt054(open("notification.xml").read())
print(f"Message ID: {summary.message_id}")
print(f"Total Entries: {summary.total_entries} | Credit: {summary.total_credit} | Debit: {summary.total_debit}")
```

---

## Public API

- `load_camt054(xml_data: str | bytes) -> list[Transaction]`: Ingests CAMT.054 XML and returns standardized `Transaction` models.
- `load_camt054_file(file_path: str | Path) -> list[Transaction]`: Loads and parses a local CAMT.054 XML file.
- `summarize_camt054(xml_data: str | bytes) -> Camt054NotificationSummary`: Returns message ID, notification counts, debits, and credits.
- `Camt054StatementParser`: Main parser class implementing `parse()` and `to_transactions()`.

---

## Supported ISO 20022 Schemas

- `urn:iso:std:iso:20022:tech:xsd:camt.054.001.02`
- `urn:iso:std:iso:20022:tech:xsd:camt.054.001.04`
- `urn:iso:std:iso:20022:tech:xsd:camt.054.001.08`
- Generic XML structures with standard `<BkToCstmrDbtCdtNtfctn>` elements

---

## Development

The project enforces strict code-quality gates: 100% test and branch coverage, strict type annotations (`mypy`), style linting (`ruff`), docstring coverage (`interrogate`), and security scanning (`bandit`).

```bash
# Run test suite with branch coverage enforcement
poetry run pytest

# Type checking and linting
poetry run mypy .
poetry run ruff check .
poetry run ruff format --check .

# Documentation and security gates
poetry run interrogate -v
poetry run bandit -r . -c pyproject.toml
```

---


## Ecosystem

`bankstatementparser` is part of a modular financial ecosystem. Optional companion packages provide specialized loaders, writers, AI agents, language servers, and transport protocol adapters:

| Package | GitHub Repository | PyPI | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`bankstatementparser`** | [`sebastienrousseau/bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser.svg)](https://pypi.org/project/bankstatementparser/) | Core Engine | Unified parser for CAMT (052/053), PAIN.001, CSV, OFX, QFX, MT940, and PDF statements |
| **`bankstatementparser-mcp`** | [`sebastienrousseau/bankstatementparser-mcp`](https://github.com/sebastienrousseau/bankstatementparser-mcp) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-mcp.svg)](https://pypi.org/project/bankstatementparser-mcp/) | AI Protocol | Model Context Protocol (MCP) server exposing statement tools to LLMs & AI agents |
| **`bankstatementparser-lsp`** | [`sebastienrousseau/bankstatementparser-lsp`](https://github.com/sebastienrousseau/bankstatementparser-lsp) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-lsp.svg)](https://pypi.org/project/bankstatementparser-lsp/) | Developer Tooling | Language Server Protocol (LSP) with live SWIFT MT940 statement validation & diagnostics |
| **`bankstatementparser-transport-ebics`** | [`sebastienrousseau/bankstatementparser-transport-ebics`](https://github.com/sebastienrousseau/bankstatementparser-transport-ebics) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-transport-ebics.svg)](https://pypi.org/project/bankstatementparser-transport-ebics/) | Transport | Automated bank statement retrieval over EBICS 3.0 (`H005`) and 2.5 (`H004`) protocols |
| **`bankstatementparser-writer-xlsx`** | [`sebastienrousseau/bankstatementparser-writer-xlsx`](https://github.com/sebastienrousseau/bankstatementparser-writer-xlsx) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-xlsx.svg)](https://pypi.org/project/bankstatementparser-writer-xlsx/) | Output Writer | Formats and exports parsed banking transactions into styled Microsoft Excel (`.xlsx`) workbooks |
| **`bankstatementparser-writer-qif`** | [`sebastienrousseau/bankstatementparser-writer-qif`](https://github.com/sebastienrousseau/bankstatementparser-writer-qif) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-qif.svg)](https://pypi.org/project/bankstatementparser-writer-qif/) | Output Writer | Serializes transactions into standard Quicken Interchange Format (`.qif`) exchange files |
| **`bankstatementparser-writer-ofx`** | [`sebastienrousseau/bankstatementparser-writer-ofx`](https://github.com/sebastienrousseau/bankstatementparser-writer-ofx) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-ofx.svg)](https://pypi.org/project/bankstatementparser-writer-ofx/) | Output Writer | Serializes transactions into standard Open Financial Exchange (`.ofx`) XML/SGML files |
| **`bankstatementparser-writer-swift`** | [`sebastienrousseau/bankstatementparser-writer-swift`](https://github.com/sebastienrousseau/bankstatementparser-writer-swift) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-swift.svg)](https://pypi.org/project/bankstatementparser-writer-swift/) | Output Writer | Exports transactions to SWIFT MT940 customer statements and MT942 interim reports |
| **`bankstatementparser-loader-bai2`** | [`sebastienrousseau/bankstatementparser-loader-bai2`](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-bai2.svg)](https://pypi.org/project/bankstatementparser-loader-bai2/) | Input Loader | Parses BAI2 cash-management and account balance statements |
| **`bankstatementparser-loader-mt942`** | [`sebastienrousseau/bankstatementparser-loader-mt942`](https://github.com/sebastienrousseau/bankstatementparser-loader-mt942) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-mt942.svg)](https://pypi.org/project/bankstatementparser-loader-mt942/) | Input Loader | Parses SWIFT MT942 interim transaction reports with credit/debit summary reconciliation |
| **`bankstatementparser-loader-cfonb`** | [`sebastienrousseau/bankstatementparser-loader-cfonb`](https://github.com/sebastienrousseau/bankstatementparser-loader-cfonb) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-cfonb.svg)](https://pypi.org/project/bankstatementparser-loader-cfonb/) | Input Loader | Parses French CFONB 120 / AFB120 120-byte fixed-width banking statement files |
| **`bankstatementparser-loader-camt054`** | [`sebastienrousseau/bankstatementparser-loader-camt054`](https://github.com/sebastienrousseau/bankstatementparser-loader-camt054) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-camt054.svg)](https://pypi.org/project/bankstatementparser-loader-camt054/) | Input Loader | Ingests ISO 20022 CAMT.054 real-time debit/credit notification stream XML |
| **`bankstatementparser-loader-sepa`** | [`sebastienrousseau/bankstatementparser-loader-sepa`](https://github.com/sebastienrousseau/bankstatementparser-loader-sepa) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-sepa.svg)](https://pypi.org/project/bankstatementparser-loader-sepa/) | Input Loader | Ingests ISO 20022 SEPA PAIN.002 payment status reports and PAIN.008 direct debit mandates |
| **`bankstatementparser-loader-bacs`** | [`sebastienrousseau/bankstatementparser-loader-bacs`](https://github.com/sebastienrousseau/bankstatementparser-loader-bacs) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-bacs.svg)](https://pypi.org/project/bankstatementparser-loader-bacs/) | Input Loader | Parses UK BACS Standard 18 / Faster Payments 106-byte fixed-width transmission files |

---

## Contributing

Contributions are welcome! Please submit an issue or pull request on GitHub. Ensure that all quality gates pass and test coverage remains at 100%.

---

## License

This project is dual-licensed under the **Apache License 2.0** and the **MIT License**. See [LICENSE-APACHE](LICENSE-APACHE) and [LICENSE-MIT](LICENSE-MIT) for full details.

