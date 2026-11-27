# bankstatementparser-loader-camt054

**camt.054** (Bank-to-Customer Debit/Credit Notification) is the
ISO 20022 XML message a bank sends to report individual bookings on an
account: one `Ntry` per booking, with one `TxDtls` per underlying
payment when the booking is a batch.

**bankstatementparser-loader-camt054** turns a camt.054 document into a
flat list of
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
`Transaction` objects (`source="camt054"`) that the rest of a
deterministic pipeline can consume unchanged.

| Concern | How this loader handles it |
| :--- | :--- |
| Versions | Namespace-agnostic: elements are matched by local name, so `camt.054.001.02` to `.08` and unnamespaced documents read the same way |
| Structure | Every `Ntfctn`, every `Ntry`, and one transaction per `TxDtls` (or one per entry without details) |
| Amounts | ISO 20022 decimals to `Decimal`, signed by `CdtDbtInd`; an entry whose amount is not a decimal is skipped |
| Codes | The bank transaction code (`BkTxCd/Prtry/Cd`, else `Domn/Cd`) as `category` `camt054:<code>` |
| Safety | Parsed with `defusedxml`: entity declarations and external references are refused |

## In this manual

- [CAMT.054 support](format.md): the public API, the element mapping
  and the sign convention.
- [The suite](suite.md): the `bankstatementparser` packages.
- [Comparison](COMPARISON.md) and [Benchmarks](BENCHMARKS.md).
- [Supported Python policy](POLICIES.md).
- [API reference](api.md): generated from the docstrings.
- [Changelog](changelog.md) and [Security policy](security.md).

The source, issues and releases live on
[GitHub](https://github.com/sebastienrousseau/bankstatementparser-loader-camt054);
the package is on
[PyPI](https://pypi.org/project/bankstatementparser-loader-camt054/).
