# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Core ISO 20022 CAMT.054 Debit/Credit Notification Loader."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as DefusedET
import pandas as pd
from bankstatementparser.base_parser import BankStatementParser
from bankstatementparser.transaction_models import Transaction

SOURCE = "camt054"


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


@dataclass(frozen=True)
class Camt054NotificationSummary:
    """Summary metrics and headers for a CAMT.054 notification message."""

    message_id: str | None
    creation_date: datetime | None
    account_id: str | None
    currency: str | None
    notification_count: int
    entry_count: int
    total_credit: Decimal
    total_debit: Decimal


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


def _process_tx_detail(
    tx_elem: ET.Element,
    base_entry: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    """Process a single TxDtls XML element within an entry."""
    row = dict(base_entry)

    # References
    e2e_id = _find_text(tx_elem, "EndToEndId")
    tx_id = _find_text(tx_elem, "TxId")
    acct_svcr_ref = _find_text(tx_elem, "AcctSvcrRef")
    mndt_id = _find_text(tx_elem, "MndtId")
    row["end_to_end_id"] = e2e_id
    row["reference"] = (
        e2e_id or tx_id or acct_svcr_ref or base_entry.get("reference")
    )
    row["mandate_id"] = mndt_id

    # Amount override if present in transaction detail
    amt_elem = None
    for child in tx_elem.iter():
        if (
            _clean_tag(child) in ("TxAmt", "Amt")
            and child.text
            and child.text.strip()
        ):
            amt_elem = child
            break
    if amt_elem is not None and amt_elem.text:
        try:
            val = Decimal(amt_elem.text.strip())
            is_credit = base_entry.get("is_credit", True)
            row["amount"] = val if is_credit else -val
            if "Ccy" in amt_elem.attrib:
                row["currency"] = amt_elem.attrib["Ccy"]
        except Exception:  # noqa: S110 # nosec B110
            pass

    # Counterparty details
    for child in tx_elem.iter():
        tag = _clean_tag(child)
        if tag == "Dbtr":
            row["debtor_name"] = _extract_party_name(child)
        elif tag == "Cdtr":
            row["creditor_name"] = _extract_party_name(child)
        elif tag == "DbtrAcct":
            row["debtor_iban"] = _extract_account_id(child)
        elif tag == "CdtrAcct":
            row["creditor_iban"] = _extract_account_id(child)

    counterparty = (
        row.get("debtor_name")
        if base_entry.get("is_credit")
        else row.get("creditor_name")
    )
    row["counterparty_name"] = counterparty

    # Remittance info
    rmt = _find_text(tx_elem, "Ustrd") or _find_text(tx_elem, "Strd")
    if rmt:
        desc = row.get("description")
        row["description"] = f"{desc} - {rmt}".strip() if desc else rmt

    results.append(row)


def _process_entry(
    ntry_elem: ET.Element,
    account_id: str | None,
    default_currency: str | None,
    results: list[dict[str, Any]],
) -> None:
    """Process a single Ntry (Entry) node in a CAMT.054 notification."""
    # Amount and Currency
    amt_elem = None
    for child in ntry_elem.iter():
        if _clean_tag(child) == "Amt" and child.text and child.text.strip():
            amt_elem = child
            break

    if amt_elem is None or not amt_elem.text:
        return

    try:
        raw_amt = Decimal(amt_elem.text.strip())
    except Exception:
        return

    currency = amt_elem.attrib.get("Ccy") or default_currency or "EUR"
    cdt_dbt = _find_text(ntry_elem, "CdtDbtInd")
    is_credit = (cdt_dbt or "").upper() == "CRDT"
    amount = raw_amt if is_credit else -raw_amt

    # Dates
    bookg_dt = _find_date(ntry_elem, "BookgDt")
    val_dt = _find_date(ntry_elem, "ValDt") or bookg_dt

    # Bank transaction code
    bk_tx_cd = _find_text(ntry_elem, "BkTxCd") or _find_text(
        ntry_elem, "Prtry"
    )
    ref = _find_text(ntry_elem, "AcctSvcrRef")

    base_entry: dict[str, Any] = {
        "account_id": account_id,
        "currency": currency,
        "amount": amount,
        "is_credit": is_credit,
        "booking_date": bookg_dt,
        "value_date": val_dt,
        "description": bk_tx_cd or "",
        "reference": ref,
        "category": f"camt054:{bk_tx_cd}" if bk_tx_cd else None,
        "counterparty_name": None,
        "end_to_end_id": None,
    }

    # Search for nested TxDtls
    tx_dtls_nodes: list[ET.Element] = []
    for child in ntry_elem.iter():
        if _clean_tag(child) == "TxDtls":
            tx_dtls_nodes.append(child)

    if tx_dtls_nodes:
        for tx_node in tx_dtls_nodes:
            _process_tx_detail(tx_node, base_entry, results)
    else:
        results.append(base_entry)


def _parse_camt054_xml(
    xml_content: str | bytes,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Parse CAMT.054 XML payload into header metadata and transaction rows."""
    if isinstance(xml_content, str):
        xml_bytes = xml_content.encode("utf-8")
    else:
        xml_bytes = xml_content

    root = DefusedET.fromstring(xml_bytes)

    header: dict[str, Any] = {
        "message_id": _find_text(root, "MsgId"),
        "creation_date": None,
        "account_id": None,
        "currency": None,
        "notification_count": 0,
    }

    cre_dt_tm = _find_text(root, "CreDtTm")
    if cre_dt_tm:
        try:
            clean_dt = cre_dt_tm.strip()
            header["creation_date"] = datetime.fromisoformat(
                clean_dt.replace("Z", "+00:00")
            )
        except Exception:  # noqa: S110 # nosec B110
            pass

    records: list[dict[str, Any]] = []

    # Find all Ntfctn nodes
    ntfctn_nodes: list[ET.Element] = []
    for child in root.iter():
        if _clean_tag(child) == "Ntfctn":
            ntfctn_nodes.append(child)

    header["notification_count"] = len(ntfctn_nodes)

    for ntfctn in ntfctn_nodes:
        acct_node = None
        for child in ntfctn.iter():
            if _clean_tag(child) == "Acct":
                acct_node = child
                break
        acct_id = _extract_account_id(acct_node)
        if acct_id and not header["account_id"]:
            header["account_id"] = acct_id

        # Find entries
        for child in ntfctn:
            if _clean_tag(child) == "Ntry":
                _process_entry(child, acct_id, header.get("currency"), records)

    return header, records


def load_camt054(xml_content: str | bytes) -> list[Transaction]:
    """Parse an ISO 20022 CAMT.054 XML notification payload into Transaction objects.

    Args:
        xml_content: XML string or raw bytes.

    Returns:
        List of Transaction instances.
    """
    _, records = _parse_camt054_xml(xml_content)
    transactions: list[Transaction] = []

    for idx, rec in enumerate(records):
        tx = Transaction(
            account_id=rec.get("account_id"),
            currency=rec.get("currency"),
            amount=rec["amount"],
            booking_date=rec.get("booking_date"),
            value_date=rec.get("value_date"),
            description=rec.get("description") or None,
            reference=rec.get("reference"),
            category=rec.get("category"),
            source=SOURCE,
            source_index=idx,
        )
        transactions.append(tx)

    return transactions


def load_camt054_file(path: str | os.PathLike[str]) -> list[Transaction]:
    """Read and parse a CAMT.054 XML file from disk.

    Args:
        path: Filesystem path to the XML file.

    Returns:
        List of Transaction instances.
    """
    data = Path(path).read_bytes()
    return load_camt054(data)


def summarize_camt054(xml_content: str | bytes) -> Camt054NotificationSummary:
    """Generate a financial summary of a CAMT.054 notification document.

    Args:
        xml_content: XML string or raw bytes.

    Returns:
        A Camt054NotificationSummary instance.
    """
    header, records = _parse_camt054_xml(xml_content)

    total_credit = Decimal("0.00")
    total_debit = Decimal("0.00")
    first_curr = None

    for rec in records:
        amt = rec["amount"]
        if not first_curr and rec.get("currency"):
            first_curr = rec["currency"]
        if amt > 0:
            total_credit += amt
        else:
            total_debit += abs(amt)

    return Camt054NotificationSummary(
        message_id=header.get("message_id"),
        creation_date=header.get("creation_date"),
        account_id=header.get("account_id"),
        currency=header.get("currency") or first_curr,
        notification_count=header.get("notification_count", 0),
        entry_count=len(records),
        total_credit=total_credit,
        total_debit=total_debit,
    )


class Camt054StatementParser(BankStatementParser):
    """BankStatementParser plugin implementation for ISO 20022 CAMT.054 XML files."""

    def __init__(self, file_name: str | Path, **kwargs: Any) -> None:
        """Initialize the CAMT.054 statement parser.

        Args:
            file_name: Path to the CAMT.054 XML file.
            **kwargs: Extra options passed to the base parser.
        """
        super().__init__(file_name, **kwargs)
        self._summary_cache: Camt054NotificationSummary | None = None

    def parse(self) -> pd.DataFrame:
        """Parse the CAMT.054 XML file into a pandas DataFrame.

        Returns:
            A pandas DataFrame containing standardized statement transactions.
        """
        txs = self.to_transactions()
        if not txs:
            return pd.DataFrame(
                columns=[
                    "date",
                    "description",
                    "amount",
                    "currency",
                    "account_id",
                    "reference",
                    "source",
                ]
            )

        records = [
            {
                "date": tx.booking_date.isoformat() if tx.booking_date else "",
                "description": tx.description or "",
                "amount": float(tx.amount),
                "currency": tx.currency,
                "account_id": tx.account_id,
                "reference": tx.reference,
                "source": tx.source,
            }
            for tx in txs
        ]
        return pd.DataFrame(records)

    def to_transactions(self) -> list[Transaction]:
        """Parse the CAMT.054 XML file into a list of Transaction models.

        Returns:
            List of parsed Transaction instances.
        """
        return load_camt054_file(self.file_name)

    def get_summary(self) -> dict[str, Any]:
        """Get summary metadata and balance metrics for the CAMT.054 notification file.

        Returns:
            Dictionary with statement statistics.
        """
        if self._summary_cache is None:
            content = Path(self.file_name).read_bytes()
            self._summary_cache = summarize_camt054(content)

        s = self._summary_cache
        return {
            "message_id": s.message_id,
            "account_id": s.account_id,
            "currency": s.currency,
            "creation_date": (
                s.creation_date.isoformat() if s.creation_date else None
            ),
            "notification_count": s.notification_count,
            "entry_count": s.entry_count,
            "total_credit": float(s.total_credit),
            "total_debit": float(s.total_debit),
        }
