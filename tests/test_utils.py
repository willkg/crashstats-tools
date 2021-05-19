# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from crashstats_tools.utils import is_crash_id_valid, parse_args, parse_crashid


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
