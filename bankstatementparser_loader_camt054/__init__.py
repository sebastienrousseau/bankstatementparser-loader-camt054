# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""ISO 20022 CAMT.054 Debit/Credit Notification Loader.

Parses ISO 20022 ``camt.054.001.xx`` bank-to-customer debit/credit notification
messages into ``bankstatementparser.transaction_models.Transaction`` objects.
"""

from __future__ import annotations

from .loader import (
    Camt054NotificationSummary,
    Camt054StatementParser,
    load_camt054,
    load_camt054_file,
    summarize_camt054,
)

__version__ = "0.0.1"
__all__ = [
    "Camt054NotificationSummary",
    "Camt054StatementParser",
    "__version__",
    "load_camt054",
    "load_camt054_file",
    "summarize_camt054",
]
