# Benchmarks

`benches/bench_load_camt054.py` measures what a camt.054 notification
costs to load as it grows along the two axes a real one grows: entries
per notification (`Ntry` under one `Ntfctn`), and transactions per
batched entry (`TxDtls` under one `Ntry`). Each transaction carries an
end-to-end id, its own amount, a debtor and a remittance line. It
times `load_camt054` and, beside it, `summarize_camt054`, which parses
the same document but builds no `Transaction` objects.

Each figure is the best of 7 runs after one untimed warm-up. Nothing
asserts a threshold: wall-clock is not comparable between machines. CI
runs `python benches/bench_load_camt054.py --quick` on every push so
the benchmark keeps running against the current API.

## Results

Run with `poetry run python benches/bench_load_camt054.py` on 2026-11-27:
Apple M1 Pro, macOS 27.2.1, CPython 3.12.16,
bankstatementparser-loader-camt054 0.0.36, bankstatementparser 0.0.35.

| Entries | Transactions each | Total | KiB | `load_camt054` ms | `summarize_camt054` ms | us per transaction |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 1 | 10 | 4.4 | 0.57 | 0.55 | 56.73 |
| 100 | 1 | 100 | 41.6 | 5.38 | 5.25 | 53.80 |
| 1000 | 1 | 1000 | 416.0 | 53.98 | 52.46 | 53.98 |
| 10000 | 1 | 10000 | 4186.5 | 580.16 | 569.30 | 58.02 |
| 100 | 100 | 10000 | 2211.9 | 329.44 | 306.29 | 32.94 |

The cost per transaction at 10,000 single-transaction entries is 1.02x
the cost at 10, so loading grows linearly with the number of entries.
A batched entry costs less per transaction (32.94 us at 100 entries of
100), because the entry-level fields are read once per entry.
`summarize_camt054` costs up to 0.98x `load_camt054`: both parse the
whole document, and the summary saves only the `Transaction` objects,
so a caller who only wants totals gains little from it.

Reproduce with `python benches/bench_load_camt054.py` (add `--json`
for machine-readable output).
