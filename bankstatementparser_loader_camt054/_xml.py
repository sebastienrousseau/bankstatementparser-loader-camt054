# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Element, text, date and amount helpers for the CAMT.054 loader."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET  # nosec B405
from datetime import date
from decimal import Decimal

# An ISO 20022 amount: unsigned ASCII digits with an optional decimal
# part (the sign is CdtDbtInd's). Decimal() also takes NaN, Infinity,
# exponents, "_" separators, a sign and other scripts' digits.
_AMOUNT = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def _parse_amount(text: str) -> Decimal | None:
    """Return ``text`` as a ``Decimal``, or ``None`` if it is no amount."""
    clean = text.strip()
    return Decimal(clean) if _AMOUNT.fullmatch(clean) else None


def _clean_tag(elem: ET.Element) -> str:
    """Extract the local XML tag name without namespace."""
    tag = elem.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_text(elem: ET.Element | None, tag_name: str) -> str | None:
    """Find text of the first descendant element matching local tag_name."""
    if elem is None:
        return None
    for child in elem.iter():
        if _clean_tag(child) == tag_name and child.text:
            val = child.text.strip()
            if val:
                return val
    return None


def _find_date(elem: ET.Element | None, parent_tag: str) -> date | None:
    """Find date inside a parent node (e.g. BookgDt/Dt or ValDt/Dt)."""
    if elem is None:
        return None
    for child in elem.iter():
        if _clean_tag(child) == parent_tag:
            dt_str = _find_text(child, "Dt") or _find_text(child, "DtTm")
            if dt_str:
                return _parse_iso_date(dt_str)
            if child.text and child.text.strip():
                return _parse_iso_date(child.text.strip())
    return None


def _parse_iso_date(date_str: str | None) -> date | None:
    """Parse ISO 8601 date string."""
    if not date_str:
        return None
    clean = date_str.strip()
    if len(clean) >= 10 and clean[4] == "-" and clean[7] == "-":
        try:
            return date.fromisoformat(clean[:10])
        except ValueError:
            return None
    return None


def _extract_account_id(acct_elem: ET.Element | None) -> str | None:
    """Extract IBAN or Other ID from an Acct XML element."""
    if acct_elem is None:
        return None
    iban = _find_text(acct_elem, "IBAN")
    if iban:
        return iban
    return _find_text(acct_elem, "Id")


def _extract_party_name(party_elem: ET.Element | None) -> str | None:
    """Extract entity name from a party XML node."""
    if party_elem is None:
        return None
    return _find_text(party_elem, "Nm")


def _first(elem: ET.Element, tag_name: str) -> ET.Element | None:
    """Return the first descendant of ``elem`` with local tag ``tag_name``."""
    return next(
        (child for child in elem.iter() if _clean_tag(child) == tag_name),
        None,
    )


def _bank_transaction_code(ntry_elem: ET.Element) -> str | None:
    """Return an entry's bank transaction code, if it has one.

    Text directly in ``BkTxCd`` or ``Prtry`` is kept for the files that
    put it there; otherwise the schema's nested ``BkTxCd/Prtry/Cd`` (the
    bank's own code) wins over ``BkTxCd/Domn/Cd`` (the domain).
    """
    flat = _find_text(ntry_elem, "BkTxCd") or _find_text(ntry_elem, "Prtry")
    bk_tx_cd = _first(ntry_elem, "BkTxCd")
    if flat or bk_tx_cd is None:
        return flat
    for parent in ("Prtry", "Domn"):
        node = _first(bk_tx_cd, parent)
        code = _find_text(node, "Cd")
        if code:
            return code
    return None
