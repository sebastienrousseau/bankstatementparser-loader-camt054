# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""A document the XML parser cannot read fails with ``ParseError``.

expat looks the declared encoding up in Python's codecs, so a document
declaring one that does not exist (found by the Atheris target:
``encoding="UT--8"``) raised ``LookupError``, and one declaring a
multi-byte codec expat cannot use (``shift_jis``, found next) raised
``ValueError``, both outside the documented failures. Each now raises ``xml.etree.ElementTree.ParseError`` like any
other document that is not well-formed.
"""

from __future__ import annotations

from collections.abc import Callable
from xml.etree.ElementTree import ParseError  # nosec B405

import pytest
from defusedxml import DefusedXmlException

from bankstatementparser_loader_camt054 import load_camt054, summarize_camt054

_DECLARED = b'<?xml version="1.0" encoding="%s"?><Document/>'


@pytest.mark.parametrize("parse", [load_camt054, summarize_camt054])
@pytest.mark.parametrize(
    ("encoding", "cause"),
    [(b"UT--8", LookupError), (b"shift_jis", ValueError)],
)
def test_unreadable_encoding_is_a_parse_error(
    parse: Callable[[bytes], object], encoding: bytes, cause: type
) -> None:
    """An unknown or multi-byte codec is ParseError, its cause kept."""
    with pytest.raises(ParseError, match="encoding") as info:
        parse(_DECLARED % encoding)
    assert isinstance(info.value.__cause__, cause)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        (b"<Document>", ParseError),
        (b"", ParseError),
        (
            b"<!DOCTYPE d [<!ENTITY e 'x'>]><Document>&e;</Document>",
            DefusedXmlException,
        ),
    ],
)
def test_documented_failures(payload: bytes, error: type[Exception]) -> None:
    """Malformed XML and entity declarations fail as documented."""
    with pytest.raises(error):
        load_camt054(payload)
