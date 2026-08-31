# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Tests for ISO 20022 CAMT.054 Debit/Credit Notification Loader."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from bankstatementparser_loader_camt054 import (
    Camt054NotificationSummary,
    Camt054StatementParser,
    __version__,
    load_camt054,
    load_camt054_file,
    summarize_camt054,
)
from bankstatementparser_loader_camt054.loader import (
    _clean_tag,
    _extract_account_id,
    _extract_party_name,
    _find_date,
    _find_text,
    _parse_iso_date,
)


def _sample_camt054_xml() -> str:
    """Return a valid ISO 20022 CAMT.054 XML notification payload."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.08">
    <BkToCstmrDbtCdtNtfctn>
        <GrpHdr>
            <MsgId>MSG-2026-CAMT054-001</MsgId>
            <CreDtTm>2026-01-15T10:30:00Z</CreDtTm>
        </GrpHdr>
        <Ntfctn>
            <Id>NTF-001</Id>
            <Acct>
                <Id>
                    <IBAN>FR7630006000011234567890189</IBAN>
                </Id>
            </Acct>
            <Ntry>
                <Amt Ccy="EUR">4500.00</Amt>
                <CdtDbtInd>CRDT</CdtDbtInd>
                <Sts>BOOK</Sts>
                <BookgDt>
                    <Dt>2026-01-15</Dt>
                </BookgDt>
                <ValDt>
                    <Dt>2026-01-15</Dt>
                </ValDt>
                <BkTxCd>
                    <Prtry>
                        <Cd>PMNT</Cd>
                    </Prtry>
                </BkTxCd>
                <NtryDtls>
                    <TxDtls>
                        <Refs>
                            <EndToEndId>E2E-REF-998877</EndToEndId>
                            <AcctSvcrRef>BANKREF123</AcctSvcrRef>
                        </Refs>
                        <AmtDtls>
                            <TxAmt>
                                <Amt Ccy="EUR">4500.00</Amt>
                            </TxAmt>
                        </AmtDtls>
                        <RltdPties>
                            <Dbtr>
                                <Nm>ACME CORP CLIENT</Nm>
                            </Dbtr>
                            <DbtrAcct>
                                <Id>
                                    <IBAN>DE89370400440532013000</IBAN>
                                </Id>
                            </DbtrAcct>
                        </RltdPties>
                        <RmtInf>
                            <Ustrd>Invoice payment INV-2026-444</Ustrd>
                        </RmtInf>
                    </TxDtls>
                </NtryDtls>
            </Ntry>
            <Ntry>
                <Amt Ccy="EUR">120.50</Amt>
                <CdtDbtInd>DBIT</CdtDbtInd>
                <Sts>BOOK</Sts>
                <BookgDt>
                    <Dt>2026-01-16</Dt>
                </BookgDt>
                <BkTxCd>
                    <Prtry>
                        <Cd>CHRG</Cd>
                    </Prtry>
                </BkTxCd>
                <AcctSvcrRef>FEEREF456</AcctSvcrRef>
            </Ntry>
        </Ntfctn>
    </BkToCstmrDbtCdtNtfctn>
</Document>
"""


def test_version() -> None:
    """Verifies that version is exposed and semantic."""
    assert __version__ == "0.0.1"


def test_load_camt054_full_payload() -> None:
    """Tests loading CAMT.054 XML with both entry-level and transaction-level details."""
    xml_str = _sample_camt054_xml()
    txs = load_camt054(xml_str)

    assert len(txs) == 2
    t1 = txs[0]
    assert t1.account_id == "FR7630006000011234567890189"
    assert t1.currency == "EUR"
    assert t1.amount == Decimal("4500.00")
    assert t1.booking_date == date(2026, 1, 15)
    assert t1.value_date == date(2026, 1, 15)
    assert t1.reference == "E2E-REF-998877"
    assert "INV-2026-444" in (t1.description or "")
    assert t1.source == "camt054"
    assert t1.source_index == 0

    t2 = txs[1]
    assert t2.account_id == "FR7630006000011234567890189"
    assert t2.amount == Decimal("-120.50")
    assert t2.booking_date == date(2026, 1, 16)
    assert t2.reference == "FEEREF456"
    assert t2.source_index == 1


def test_summarize_camt054() -> None:
    """Tests summary extraction for CAMT.054."""
    xml_str = _sample_camt054_xml()
    summary = summarize_camt054(xml_str)

    assert isinstance(summary, Camt054NotificationSummary)
    assert summary.message_id == "MSG-2026-CAMT054-001"
    assert summary.account_id == "FR7630006000011234567890189"
    assert summary.currency == "EUR"
    assert summary.notification_count == 1
    assert summary.entry_count == 2
    assert summary.total_credit == Decimal("4500.00")
    assert summary.total_debit == Decimal("120.50")


def test_camt054_statement_parser_class(tmp_path: Path) -> None:
    """Tests Camt054StatementParser BankStatementParser protocol implementation."""
    sample_file = tmp_path / "notification.xml"
    sample_file.write_text(_sample_camt054_xml(), encoding="utf-8")

    parser = Camt054StatementParser(sample_file)
    df = parser.parse()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "amount" in df.columns
    assert "date" in df.columns
    assert "account_id" in df.columns

    summary = parser.get_summary()
    assert summary["message_id"] == "MSG-2026-CAMT054-001"
    assert summary["account_id"] == "FR7630006000011234567890189"
    assert summary["entry_count"] == 2
    assert summary["total_credit"] == 4500.00
    assert summary["total_debit"] == 120.50


def test_camt054_statement_parser_empty(tmp_path: Path) -> None:
    """Tests parser behavior with empty notification."""
    empty_xml = (
        "<Document><BkToCstmrDbtCdtNtfctn></BkToCstmrDbtCdtNtfctn></Document>"
    )
    empty_file = tmp_path / "empty.xml"
    empty_file.write_text(empty_xml, encoding="utf-8")

    parser = Camt054StatementParser(empty_file)
    df = parser.parse()
    assert len(df) == 0
    assert "amount" in df.columns

    summary = parser.get_summary()
    assert summary["entry_count"] == 0
    assert summary["notification_count"] == 0


def test_helper_functions() -> None:
    """Tests XML traversal helper functions and edge cases."""
    elem = ET.Element("{urn:test}SampleNode")
    elem.text = "  hello world  "
    assert _clean_tag(elem) == "SampleNode"
    assert _find_text(elem, "SampleNode") == "hello world"
    assert _find_text(None, "Any") is None
    assert _extract_account_id(None) is None
    assert _extract_party_name(None) is None

    other_acct = ET.Element("Acct")
    id_node = ET.SubElement(other_acct, "Id")
    id_node.text = "ACC-OTHER-123"
    assert _extract_account_id(other_acct) == "ACC-OTHER-123"

    party = ET.Element("Party")
    nm = ET.SubElement(party, "Nm")
    nm.text = "Company Ltd"
    assert _extract_party_name(party) == "Company Ltd"

    assert _parse_iso_date("2026-02-28") == date(2026, 2, 28)
    assert _parse_iso_date("invalid-date-format") is None
    assert _parse_iso_date("2026-99-99") is None
    assert _parse_iso_date("") is None

    # Test direct text in date node
    d_elem = ET.Element("BookgDt")
    d_elem.text = "2026-03-01"
    assert _find_date(d_elem, "BookgDt") == date(2026, 3, 1)
    assert _find_date(None, "Any") is None


def test_debit_tx_detail_and_creditor_account() -> None:
    """Tests debit transaction detail with Cdtr and CdtrAcct extraction."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.08">
    <BkToCstmrDbtCdtNtfctn>
        <GrpHdr>
            <CreDtTm>invalid-iso-datetime</CreDtTm>
        </GrpHdr>
        <Ntfctn>
            <Ntry>
                <Amt Ccy="USD">999.00</Amt>
                <CdtDbtInd>DBIT</CdtDbtInd>
                <NtryDtls>
                    <TxDtls>
                        <AmtDtls>
                            <TxAmt>
                                <Amt Ccy="USD">999.00</Amt>
                            </TxAmt>
                        </AmtDtls>
                        <RltdPties>
                            <Cdtr>
                                <Nm>SUPPLIER CORP</Nm>
                            </Cdtr>
                            <CdtrAcct>
                                <Id>
                                    <IBAN>GB29NWBK60161331926819</IBAN>
                                </Id>
                            </CdtrAcct>
                        </RltdPties>
                    </TxDtls>
                </NtryDtls>
            </Ntry>
        </Ntfctn>
    </BkToCstmrDbtCdtNtfctn>
</Document>
"""
    txs = load_camt054(xml_str)
    assert len(txs) == 1
    assert txs[0].amount == Decimal("-999.00")
    assert txs[0].currency == "USD"


def test_invalid_entry_amount_and_detail_amount_handling() -> None:
    """Tests that missing or invalid amount entry is skipped gracefully."""
    xml_str = """<Document><BkToCstmrDbtCdtNtfctn><Ntfctn>
        <Ntry><Amt>invalid-amount</Amt></Ntry>
        <Ntry></Ntry>
        <Ntry>
            <Amt Ccy="EUR">50.00</Amt>
            <NtryDtls>
                <TxDtls>
                    <AmtDtls>
                        <TxAmt>
                            <Amt>not-a-number</Amt>
                        </TxAmt>
                    </AmtDtls>
                    <RmtInf>
                        <Ustrd>Direct Remittance</Ustrd>
                    </RmtInf>
                </TxDtls>
            </NtryDtls>
        </Ntry>
    </Ntfctn></BkToCstmrDbtCdtNtfctn></Document>"""
    txs = load_camt054(xml_str)
    assert len(txs) == 1
    assert txs[0].amount == Decimal("-50.00")
    assert "Direct Remittance" in (txs[0].description or "")


def test_load_camt054_file(tmp_path: Path) -> None:
    """Tests load_camt054_file helper."""
    f = tmp_path / "test.xml"
    f.write_text(_sample_camt054_xml(), encoding="utf-8")
    txs = load_camt054_file(f)
    assert len(txs) == 2


@given(st.text(min_size=1, max_size=50))
def test_fuzz_clean_tag(tag_suffix: str) -> None:
    """Property-based fuzzing of tag cleaner."""
    elem = ET.Element(f"{{urn:iso:std:test}}{tag_suffix}")
    assert _clean_tag(elem) == tag_suffix
