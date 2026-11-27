<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# bankstatementparser-loader-camt054 Architecture

A map of the codebase for new contributors and maintainers: how a
camt.054 notification becomes `Transaction` objects, and where to
change what.

## The pipeline

```text
camt.054 XML (str, bytes, or file)
        |  _parse_camt054_xml: defusedxml.ElementTree.fromstring
        |    GrpHdr          -> MsgId, CreDtTm (header)
        |    each Ntfctn     -> Acct (IBAN, else the first Id)
        |      each Ntry     -> _process_entry (amount, sign, dates, code)
        |        each TxDtls -> _process_tx_detail (references, own amount,
        |                       parties, remittance)
        v
(header dict, list of row dicts)
        |
        +--> load_camt054       -> list[Transaction] (source="camt054")
        +--> summarize_camt054  -> Camt054NotificationSummary
```

`load_camt054_file` reads a path as bytes, so the document's own
encoding declaration applies, and calls `load_camt054`.
`Camt054StatementParser`, the plugin the core finds through the
`camt054` and `camt_054` entry points, wraps the same functions for the
core's `parse()` (a pandas DataFrame), `to_transactions()` and
`get_summary()` (cached after the first read).

## Modules

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Loader** | `bankstatementparser_loader_camt054/loader.py` | Document, notification, entry and detail walk; `load_camt054` / `load_camt054_file` / `summarize_camt054`; `Camt054NotificationSummary`; `Camt054StatementParser` |
| **XML helpers** | `bankstatementparser_loader_camt054/_xml.py` | Local tag names, text and date lookup, ISO 20022 amount check (`_parse_amount`), account and party extraction, the bank transaction code |
| **Package entry** | `bankstatementparser_loader_camt054/__init__.py` | Re-exports the public API and defines `__version__` (single source of truth) |
| **Tests** | `tests/` | 100% line + branch coverage: unit tests, amounts, bank transaction codes, the golden fixture, docs accuracy, examples, release notes and the shared suite conformance gate |
| **Fuzzing** | `fuzz/fuzz_load_camt054.py`, `fuzz/corpus/` | Atheris target for `load_camt054` and `summarize_camt054`, run by the CI `Fuzz` job |
| **Benchmarks** | `benches/bench_load_camt054.py` | Load and summary cost as a notification grows; `--quick` runs in CI |
| **Examples** | `examples/` | Two runnable scripts: loading and summarising, and batch processing |
| **Manual** | `mkdocs.yml`, `docs/` | The MkDocs Material user manual and API reference, deployed to GitHub Pages |
| **Scripts** | `scripts/` | `verify_versions.py`, `release_notes.py`, `export_locked_requirements.py`, `check_complexity.py`, `check_suite_consistency.py`, `readme-check.sh` |

## Key design decisions

- **Local names, not namespaces.** Every lookup strips the namespace,
  so one code path reads every camt.054 version.
- **Decimal everywhere.** An amount must be unsigned ASCII digits with
  an optional fraction before it becomes a `Decimal`; the sign comes
  from `CdtDbtInd`. An entry whose amount is not one is skipped, and a
  detail amount that is not one is ignored.
- **One row per payment.** A batched entry yields one transaction per
  `TxDtls`, each with its own amount when it carries one.
- **defusedxml** parses every document, so entity expansion and
  external references are refused before any element is read.
- **Coverage enforced at 100%** line + branch and docstring, and the
  suite's complexity ceilings with a baseline that may only shrink.

## Extension points

- **A new field on the transaction:** read it in `_process_entry` or
  `_process_tx_detail` and pass it on in `load_camt054`.
- **A new summary field:** extend `Camt054NotificationSummary`,
  `summarize_camt054` and `Camt054SummaryRecord`.
