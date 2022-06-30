# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import operator

import pytest

from crashstats_tools.utils import (
    escape_whitespace,
    INFINITY,
    is_crash_id_valid,
    parse_args,
    parse_crashid,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        (None, ""),
        ("", ""),
        ("abc", "abc"),
        ("abc\tdef", "abc\\tdef"),
        ("abc\rdef", "abc\\rdef"),
        ("abc\ndef", "abc\\ndef"),
    ],
)
def test_escape_whitespace(text, expected):
    assert escape_whitespace(text) == expected


@pytest.mark.parametrize(
    "crashid, expected",
    [
        ("", False),
        ("aaa", False),
        ("de1bb258cbbf4589a67334f800160918", False),
        ("DE1BB258-CBBF-4589-A673-34F800160918", False),
        ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", False),
        ("00000000-0000-0000-0000-000000000000", True),
    ],
)
def test_validate_crash_id(crashid, expected):
    assert is_crash_id_valid(crashid) == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], {}),
        (["--foo", "bar"], {"foo": ["bar"]}),
        (["--foo=bar"], {"foo": ["bar"]}),
        (["--foo=bar1", "--foo=bar2"], {"foo": ["bar1", "bar2"]}),
    ],
)
def test_parse_args(args, expected):
    assert parse_args(args) == expected


@pytest.mark.parametrize(
    "item, expected",
    [
        (
            "0b794045-87ec-4649-9ce1-73ec10191120",
            "0b794045-87ec-4649-9ce1-73ec10191120",
        ),
        (
            "bp-0b794045-87ec-4649-9ce1-73ec10191120",
            "0b794045-87ec-4649-9ce1-73ec10191120",
        ),
        (
            "https://crash-stats.mozilla.org/report/index/0b794045-87ec-4649-9ce1-73ec10191120",
            "0b794045-87ec-4649-9ce1-73ec10191120",
        ),
    ],
)
def test_parse_crashid(item, expected):
    assert parse_crashid(item) == expected


@pytest.mark.parametrize("item", ["", "foo"])
def test_parse_crashid_badids(item):
    with pytest.raises(ValueError):
        parse_crashid(item)


@pytest.mark.parametrize(
    "oper, rhs, expected",
    [
        # Infinity == x
        (operator.eq, 10000, False),
        (operator.eq, INFINITY, True),
        # Infinity != x
        (operator.ne, 10000, True),
        (operator.ne, INFINITY, False),
        # Infinity < x
        (operator.lt, 10000, False),
        (operator.lt, INFINITY, False),
        # Infinity <= x
        (operator.le, 10000, False),
        (operator.le, INFINITY, True),
        # Infinity > x
        (operator.gt, 10000, True),
        (operator.gt, INFINITY, False),
        # Infinity >= x
        (operator.ge, 10000, True),
        (operator.ge, INFINITY, True),
    ],
)
def test_infinity_comparisons(oper, rhs, expected):
    assert oper(INFINITY, rhs) == expected


def test_infinity_lhs_subtraction():
    assert INFINITY - 5 == INFINITY
    assert INFINITY - INFINITY == 0


def test_infinity_rhs_subtraction():
    with pytest.raises(ValueError):
        5 - INFINITY
