# Comparison

Where bankstatementparser-loader-camt054 fits next to the camt.054
reader a `bankstatementparser` user already has. Both were run on
`tests/fixtures/notification.xml` on 2026-11-27: a credit entry
batching two transfers (each `TxDtls` with its own amount) and a Direct
Debit entry. Nothing here is a measured ranking.

| Project | Rows for the fixture | Batched entry | Bank transaction code | Output |
| :--- | :--- | :--- | :--- | :--- |
| **bankstatementparser-loader-camt054** 0.0.36 | 3 | One row per `TxDtls`: 1000.00 and 250.00, each with its `EndToEndId` and remittance | `category` `camt054:SEPA-CT` | `Transaction` objects, a summary, or a DataFrame through the core's plugin interface |
| [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) 0.0.35 `Camt054Parser` | 2 | One row of 1250.00 with the first `EndToEndId` and both remittance texts joined | Not read | A DataFrame from `parse()` |

Evidence: `bankstatementparser/camt_reports.py` in the core
(`Camt054Parser`, a streaming reader shared with `Camt052Parser`), and
`bankstatementparser_loader_camt054/loader.py` here.

## When each fits

- **bankstatementparser-loader-camt054**: you reconcile individual
  payments inside batched bookings, or want the bank transaction code.
- **`bankstatementparser` `Camt054Parser`**: one row per booking is
  what you need, and you want no extra package; it streams, so it also
  suits very large documents.

The wider family is listed in [The suite](suite.md).
