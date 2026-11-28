# Changelog

All notable changes to `bankstatementparser-loader-camt054` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.37] - 2026-11-28

### Changed

- CI: four pinned actions move to their latest releases:
  codeql-action 4.39.5, markdownlint-cli2-action 25.1.0,
  cosign-installer 4.1.4 and sbom-action 0.24.4.

### Fixed

- The suite consistency check authenticates its GitHub API request
  with the workflow token, so the shared anonymous rate limit no
  longer fails it.

## [0.0.36] - 2026-11-27

### Fixed

- A schema-valid notification now has a category: the loader read the
  bank transaction code only as text directly inside `BkTxCd` or
  `Prtry`, but ISO 20022 nests it (`BkTxCd/Prtry/Cd`,
  `BkTxCd/Domn/Cd`). Entries carrying a code gain
  `category="camt054:<code>"`, and their description starts with the
  code, as the loader always intended.
- An amount that is not an ISO 20022 decimal (unsigned ASCII digits
  with an optional fraction) is now treated like any other unreadable
  amount: the entry is skipped, or a detail amount ignored. Before,
  `NaN` and `Infinity` escaped `load_camt054` as a pydantic
  `ValidationError` and `summarize_camt054` as
  `decimal.InvalidOperation` or an infinite total, `1e5` loaded as
  100000, and `-5` on a credit as a debit.
- A document declaring an encoding Python does not know (for example
  `encoding="UT--8"`) or a multi-byte one expat cannot use (for example
  `shift_jis`) now raises `xml.etree.ElementTree.ParseError`, like any
  other document that is not well-formed, instead of `LookupError` or
  `ValueError`. Found by the new Atheris target.

### Added

- An Atheris fuzz target, `fuzz/fuzz_load_camt054.py`, for
  `load_camt054` and `summarize_camt054`, with a seed corpus; it fails
  on any exception but the XML parser's documented ones, on a malformed
  `Transaction` and on a summary that disagrees with the load. CI runs
  it for 120 s on every change; `make fuzz` locally.
- `benches/bench_load_camt054.py`, a real benchmark of `load_camt054`
  and `summarize_camt054` along entries per notification and
  transactions per batched entry, replacing a file that timed an empty
  loop. CI runs `--quick`; `docs/BENCHMARKS.md` records a full run with
  its environment.
- `tests/fixtures/notification.xml`, a camt.054.001.08 notification,
  with a golden test.
- A `Makefile` wrapping the local gates (`make check`).
- A MkDocs Material user manual (`mkdocs.yml`, `docs/`) with an
  mkdocstrings API reference, built with `--strict` on every pull
  request and deployed to GitHub Pages from `main`
  (`.github/workflows/docs.yml`, `make docs`). It replaces a Sphinx
  configuration that nothing built.
- `ARCHITECTURE.md`, `CODE_OF_CONDUCT.md`, `docs/POLICIES.md`,
  `docs/BENCHMARKS.md`, `docs/COMPARISON.md`, `docs/format.md` and
  `docs/suite.md`.
- Signed releases: keyless cosign `.sig` and `.pem` per distribution,
  SLSA provenance
  (`bankstatementparser-loader-camt054-vX.Y.Z.intoto.jsonl`,
  slsa-github-generator 2.1.0), CycloneDX and SPDX SBOMs and a licence
  manifest on every GitHub release, and PEP 740 attestations on PyPI.
- The OpenSSF Scorecard workflow, the suite's Docs Lint workflow
  (`scripts/readme-check.sh` and markdownlint), a Security workflow
  (Bandit and `pip-audit` on every locked set), the portfolio pull
  request and issue templates, and `.github/demo.gif` rendered by
  `make demo` from `.github/demo.tape`.
- Hash-pinned requirement sets exported from the lock
  (`requirements/{runtime,ci,fuzz,docs}.txt`, by the suite's
  `scripts/export_locked_requirements.py`) and compiled release tooling
  (`requirements/{build,sbom}.txt`).

### Changed

- Require `bankstatementparser >= 0.0.35`, the newest core release, and
  align the version with the suite's 0.0.36 release; `poetry.lock`
  moves core to 0.0.35.
- Dev tools: ruff 0.17.6, mypy 2.4.1, pytest 9.2.0, hypothesis 6.168.5,
  tomli 2.5.0 and pytest-benchmark 5.3.1 (Dependabot #4 to #9).
- The XML helpers move from `loader.py` to `_xml.py`, keeping
  `loader.py` under the suite's 500-line ceiling.
- CI pins every action by commit SHA, installs only the hashed lock
  exports, and tests CPython 3.10 to 3.14 on Ubuntu, macOS and Windows.
  Write permissions sit on the jobs that need them.
- `README.md` follows the portfolio template; its Quick Start is run
  by the tests. It no longer claims the loader extracts `InstrId` or
  supports only listed schema versions (it matches local names, so any
  version reads). The suite table moves to `docs/suite.md`.
  `CONTRIBUTING.md` describes the steps that work in this repository.

## [0.0.35] - 2026-11-26

The first release on PyPI. Versions 0.0.20 to 0.0.34 were never
released: the package joins the bankstatementparser suite, which ships
one version across every package, at 0.0.35.

### Added

- `.github/workflows/release.yml`: a `v*` tag builds the sdist and
  wheel, publishes them to PyPI by trusted publishing, attaches them to
  a GitHub release and writes its notes with `scripts/release_notes.py`
  from the highlights in `.github/releases/<tag>.md`.
- `.github/workflows/pr.yml` (PR Gate) and
  `.github/workflows/suite-consistency.yml`, a daily check that every
  suite package on PyPI agrees on one version
  (`scripts/check_suite_consistency.py`).
- `scripts/verify_versions.py` and the suite's shared
  `tests/test_suite_conformance.py` and `tests/test_release_notes.py`.
- `.github/dependabot.yml`: weekly pip and GitHub Actions updates.
- `scripts/check_complexity.py`, the suite's complexity gate, with
  `scripts/complexity_baseline.json`: per-function ceilings
  (cyclomatic 10, cognitive 15, Halstead 30, 60 lines; 500 lines per
  file), run in CI's lint job. Functions already over a ceiling are
  baselined and may not get worse.
- `.github/workflows/codeql.yml`: CodeQL as an advanced setup for
  Python and GitHub Actions, on pushes and pull requests to `main`
  and weekly.

### Changed

- Requires `bankstatementparser >= 0.0.34` (was `>= 0.0.18`).
- The coverage gate measures branches (`--cov-branch`). Three branches
  in `loader.py` that no test took are now covered; coverage is 100%
  with branches counted.
- Dev dependency floor `pytest >= 9.0.3`, the release that fixes
  PYSEC-2026-1845; `tomli` (Python < 3.11) and `packaging` declared for
  the conformance test.
- GitHub Actions: `actions/checkout` v7, `actions/setup-python` v7.

### Fixed

- `get_summary()` returns `Camt054SummaryRecord`, a `SummaryRecord` subtype carrying the
  same keys as before (message and account ids, currency, creation date, notification and entry counts, and credit and debit totals), so the override matches the core parser's
  `SummaryRecord` contract and `mypy` passes against bankstatementparser 0.0.29.

## [0.0.19] - 2026-09-01

### Added

- Initial production release of `bankstatementparser-loader-camt054`: ISO 20022 CAMT.054 Real-Time Notification Loader.
- 100% statement and branch test coverage.
- High-concurrency throughput testing (>10,000 TPS) with sub-second response times.
- Strict type hints (`mypy --strict`) and ruff linting.
- Integration with the core `bankstatementparser` ecosystem.
