# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from textwrap import dedent

from click.testing import CliRunner
import freezegun
import pytest
import responses

from crashstats_tools import cmd_supersearchfacet
from crashstats_tools.utils import DEFAULT_HOST


def test_it_runs():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--help"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_host():
    host = "http://example.com"
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        host + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--host=" + host, "--_facets=product", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.stdout == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_token():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=tab"],
        env={"CRASHSTATS_API_TOKEN": api_token, "COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_dates():
    start_date = "2022-06-01"
    end_date = "2022-06-14"
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=" + start_date, "<" + end_date],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=tab",
            "--start-date=" + start_date,
            "--end-date=" + end_date,
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_relative_date():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-28", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=tab",
            "--end-date=2022-07-01",
            "--relative-range=3d",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_denote_weekends():
    supersearch_data = {
        "hits": [],
        "total": 837148,
        "facets": {
            "histogram_date": [
                {
                    "term": "2022-06-24T00:00:00+00:00",
                    "count": 130824,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62097},
                            {"term": "Fenix", "count": 49585},
                            {"term": "Thunderbird", "count": 18202},
                            {"term": "Focus", "count": 938},
                            {"term": "MozillaVPN", "count": 1},
                            {"term": "ReferenceBrowser", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-25T00:00:00+00:00",
                    "count": 129534,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 60180},
                            {"term": "Fenix", "count": 49559},
                            {"term": "Thunderbird", "count": 18888},
                            {"term": "Focus", "count": 907},
                        ]
                    },
                },
                {
                    "term": "2022-06-26T00:00:00+00:00",
                    "count": 127166,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 59486},
                            {"term": "Fenix", "count": 48276},
                            {"term": "Thunderbird", "count": 18532},
                            {"term": "Focus", "count": 871},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-27T00:00:00+00:00",
                    "count": 122340,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 55451},
                            {"term": "Fenix", "count": 49019},
                            {"term": "Thunderbird", "count": 16913},
                            {"term": "Focus", "count": 957},
                        ]
                    },
                },
                {
                    "term": "2022-06-28T00:00:00+00:00",
                    "count": 99098,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 49089},
                            {"term": "Firefox", "count": 41220},
                            {"term": "Thunderbird", "count": 7858},
                            {"term": "Focus", "count": 931},
                        ]
                    },
                },
                {
                    "term": "2022-06-29T00:00:00+00:00",
                    "count": 96583,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 50284},
                            {"term": "Firefox", "count": 38363},
                            {"term": "Thunderbird", "count": 7040},
                            {"term": "Focus", "count": 895},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-30T00:00:00+00:00",
                    "count": 131603,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62530},
                            {"term": "Fenix", "count": 49355},
                            {"term": "Thunderbird", "count": 18934},
                            {"term": "Focus", "count": 784},
                        ]
                    },
                },
            ],
        },
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_histogram.date": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_histogram.date=product",
            "--relative-range=7d",
            "--denote-weekends",
            "--format=tab",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        histogram_date.product
        histogram_date\tFenix\tFirefox\tFocus\tMozillaVPN\tReferenceBrowser\tThunderbird\ttotal
        2022-06-24\t49585\t62097\t938\t1\t1\t18202\t130824
        2022-06-25 **\t49559\t60180\t907\t0\t0\t18888\t129534
        2022-06-26 **\t48276\t59486\t871\t1\t0\t18532\t127166
        2022-06-27\t49019\t55451\t957\t0\t0\t16913\t122340
        2022-06-28\t49089\t41220\t931\t0\t0\t7858\t99098
        2022-06-29\t50284\t38363\t895\t1\t0\t7040\t96583
        2022-06-30\t49355\t62530\t784\t0\t0\t18934\t131603
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_supersearch_url():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {"_facets": "product", "date": ">=2022-06-30", "_results_number": "0"}
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--format=tab",
            (
                "--supersearch-url=https://crash-stats.mozilla.org"
                + "/api/SuperSearch/?"
                + "date=%3E%3D2022-06-30&"
                + "_facets=product"
            ),
        ],
        env={"COLUMNS": "100"},
    )
    print(result.output)
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@pytest.mark.parametrize(
    "data, expected",
    [
        pytest.param({}, {}, id="empty_data"),
        pytest.param(
            {
                "product": [
                    {"term": "Firefox", "count": 353039},
                    {"term": "Fenix", "count": 228578},
                ]
            },
            {
                "product": [
                    {"product": "Firefox", "count": 353039},
                    {"product": "Fenix", "count": 228578},
                ]
            },
            id="_facets=product",
        ),
        pytest.param(
            {
                "cardinality_product": {"value": 6},
            },
            {"cardinality_product": [{"cardinality_product": "value", "value": 6}]},
            id="_facets=_cardinality.product",
        ),
        pytest.param(
            {
                "histogram_date": [
                    {
                        "term": "2023-12-21T00:00:00+00:00",
                        "count": 116333,
                        "facets": {
                            "product": [
                                {"term": "Firefox", "count": 67152},
                                {"term": "Fenix", "count": 33123},
                            ]
                        },
                    },
                    {
                        "term": "2023-12-22T00:00:00+00:00",
                        "count": 106095,
                        "facets": {
                            "product": [
                                {"term": "Firefox", "count": 59209},
                                {"term": "Fenix", "count": 32674},
                            ]
                        },
                    },
                ],
            },
            {
                "histogram_date": {
                    "product": [
                        {
                            "histogram_date": "2023-12-21",
                            "Fenix": 33123,
                            "Firefox": 67152,
                            "total": 116333,
                        },
                        {
                            "histogram_date": "2023-12-22",
                            "Fenix": 32674,
                            "Firefox": 59209,
                            "total": 106095,
                        },
                    ],
                },
            },
            id="_histogram.date=product",
        ),
        pytest.param(
            {
                "histogram_date": [
                    {
                        "term": "2023-12-21T00:00:00+00:00",
                        "count": 116333,
                        "facets": {"cardinality_product": {"value": 5}},
                    },
                    {
                        "term": "2023-12-22T00:00:00+00:00",
                        "count": 106095,
                        "facets": {"cardinality_product": {"value": 4}},
                    },
                ],
            },
            {
                "histogram_date": {
                    "cardinality_product": [
                        {"histogram_date": "2023-12-21", "value": 5},
                        {"histogram_date": "2023-12-22", "value": 4},
                    ],
                },
            },
            id="_histogram.date=_cardinality.product",
        ),
        pytest.param(
            {
                "product": [
                    {
                        "term": "Firefox",
                        "count": 353039,
                        "facets": {
                            "release_channel": [
                                {"term": "release", "count": 153412},
                                {"term": "nightly", "count": 10660},
                            ],
                        },
                    },
                    {
                        "term": "Fenix",
                        "count": 228578,
                        "facets": {
                            "release_channel": [
                                {"term": "release", "count": 216877},
                                {"term": "nightly", "count": 6423},
                            ]
                        },
                    },
                ],
            },
            {
                "product / release_channel": [
                    {
                        "product / release_channel": "Firefox / release",
                        "count": 153412,
                    },
                    {
                        "product / release_channel": "Firefox / nightly",
                        "count": 10660,
                    },
                    {
                        "product / release_channel": "Fenix / release",
                        "count": 216877,
                    },
                    {
                        "product / release_channel": "Fenix / nightly",
                        "count": 6423,
                    },
                ]
            },
            id="_aggs.product=release_channel",
        ),
        pytest.param(
            {
                "product": [
                    {
                        "term": "Firefox",
                        "count": 384339,
                        "facets": {
                            "version": [
                                {
                                    "term": "115.9.1esr",
                                    "count": 116326,
                                    "facets": {
                                        "cardinality_install_time": {"value": 63255}
                                    },
                                },
                                {
                                    "term": "124.0.1",
                                    "count": 90916,
                                    "facets": {
                                        "cardinality_install_time": {"value": 78342}
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "term": "Fenix",
                        "count": 184059,
                        "facets": {
                            "version": [
                                {
                                    "term": "124.1.0",
                                    "count": 49726,
                                    "facets": {
                                        "cardinality_install_time": {"value": 31191}
                                    },
                                },
                                {
                                    "term": "124.2.0",
                                    "count": 21083,
                                    "facets": {
                                        "cardinality_install_time": {"value": 7776}
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
            {
                "product / version / cardinality_install_time": [
                    {
                        "count": 63255,
                        "product / version / cardinality_install_time": "Firefox / 115.9.1esr / value",
                    },
                    {
                        "count": 78342,
                        "product / version / cardinality_install_time": "Firefox / 124.0.1 / value",
                    },
                    {
                        "count": 31191,
                        "product / version / cardinality_install_time": "Fenix / 124.1.0 / value",
                    },
                    {
                        "count": 7776,
                        "product / version / cardinality_install_time": "Fenix / 124.2.0 / value",
                    },
                ],
            },
            id="_aggs.product.version=_cardinality.install_time",
        ),
    ],
)
def test_flatten_facets(data, expected):
    assert cmd_supersearchfacet.flatten_facets(data) == expected


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_facet_product():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_facet_product_with_leftovers():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=tab", "--leftover-count"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
        total\t19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_cardinality_product():
    supersearch_data = {
        "hits": [],
        "total": 837148,
        "facets": {"cardinality_product": {"value": 6}},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "_cardinality.product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=_cardinality.product", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        cardinality_product
        cardinality_product\tvalue
        value\t6
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_histogram_date_product():
    supersearch_data = {
        "hits": [],
        "total": 837148,
        "facets": {
            "histogram_date": [
                {
                    "term": "2022-06-24T00:00:00+00:00",
                    "count": 130824,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62097},
                            {"term": "Fenix", "count": 49585},
                            {"term": "Thunderbird", "count": 18202},
                            {"term": "Focus", "count": 938},
                            {"term": "MozillaVPN", "count": 1},
                            {"term": "ReferenceBrowser", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-25T00:00:00+00:00",
                    "count": 129534,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 60180},
                            {"term": "Fenix", "count": 49559},
                            {"term": "Thunderbird", "count": 18888},
                            {"term": "Focus", "count": 907},
                        ]
                    },
                },
                {
                    "term": "2022-06-26T00:00:00+00:00",
                    "count": 127166,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 59486},
                            {"term": "Fenix", "count": 48276},
                            {"term": "Thunderbird", "count": 18532},
                            {"term": "Focus", "count": 871},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-27T00:00:00+00:00",
                    "count": 122340,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 55451},
                            {"term": "Fenix", "count": 49019},
                            {"term": "Thunderbird", "count": 16913},
                            {"term": "Focus", "count": 957},
                        ]
                    },
                },
                {
                    "term": "2022-06-28T00:00:00+00:00",
                    "count": 99098,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 49089},
                            {"term": "Firefox", "count": 41220},
                            {"term": "Thunderbird", "count": 7858},
                            {"term": "Focus", "count": 931},
                        ]
                    },
                },
                {
                    "term": "2022-06-29T00:00:00+00:00",
                    "count": 96583,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 50284},
                            {"term": "Firefox", "count": 38363},
                            {"term": "Thunderbird", "count": 7040},
                            {"term": "Focus", "count": 895},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-30T00:00:00+00:00",
                    "count": 131603,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62530},
                            {"term": "Fenix", "count": 49355},
                            {"term": "Thunderbird", "count": 18934},
                            {"term": "Focus", "count": 784},
                        ]
                    },
                },
            ],
        },
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_histogram.date": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_histogram.date=product", "--relative-range=1w", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        histogram_date.product
        histogram_date\tFenix\tFirefox\tFocus\tMozillaVPN\tReferenceBrowser\tThunderbird\ttotal
        2022-06-24\t49585\t62097\t938\t1\t1\t18202\t130824
        2022-06-25\t49559\t60180\t907\t0\t0\t18888\t129534
        2022-06-26\t48276\t59486\t871\t1\t0\t18532\t127166
        2022-06-27\t49019\t55451\t957\t0\t0\t16913\t122340
        2022-06-28\t49089\t41220\t931\t0\t0\t7858\t99098
        2022-06-29\t50284\t38363\t895\t1\t0\t7040\t96583
        2022-06-30\t49355\t62530\t784\t0\t0\t18934\t131603
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_histogram_date_product_with_leftover():
    supersearch_data = {
        "hits": [],
        "total": 837148,
        "facets": {
            "histogram_date": [
                {
                    "term": "2022-06-24T00:00:00+00:00",
                    "count": 130824,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62097},
                            {"term": "Fenix", "count": 49585},
                            {"term": "Thunderbird", "count": 18202},
                            {"term": "Focus", "count": 938},
                            {"term": "MozillaVPN", "count": 1},
                            {"term": "ReferenceBrowser", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-25T00:00:00+00:00",
                    "count": 129534,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 60180},
                            {"term": "Fenix", "count": 49559},
                            {"term": "Thunderbird", "count": 18888},
                            {"term": "Focus", "count": 907},
                        ]
                    },
                },
                {
                    "term": "2022-06-26T00:00:00+00:00",
                    "count": 127166,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 59486},
                            {"term": "Fenix", "count": 48276},
                            {"term": "Thunderbird", "count": 18532},
                            {"term": "Focus", "count": 871},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-27T00:00:00+00:00",
                    "count": 122340,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 55451},
                            {"term": "Fenix", "count": 49019},
                            {"term": "Thunderbird", "count": 16913},
                            {"term": "Focus", "count": 957},
                        ]
                    },
                },
                {
                    "term": "2022-06-28T00:00:00+00:00",
                    "count": 99098,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 49089},
                            {"term": "Firefox", "count": 41220},
                            {"term": "Thunderbird", "count": 7858},
                            {"term": "Focus", "count": 931},
                        ]
                    },
                },
                {
                    "term": "2022-06-29T00:00:00+00:00",
                    "count": 96583,
                    "facets": {
                        "product": [
                            {"term": "Fenix", "count": 50284},
                            {"term": "Firefox", "count": 38363},
                            {"term": "Thunderbird", "count": 7040},
                            {"term": "Focus", "count": 895},
                            {"term": "MozillaVPN", "count": 1},
                        ]
                    },
                },
                {
                    "term": "2022-06-30T00:00:00+00:00",
                    "count": 131603,
                    "facets": {
                        "product": [
                            {"term": "Firefox", "count": 62530},
                            {"term": "Fenix", "count": 49355},
                            {"term": "Thunderbird", "count": 18934},
                            {"term": "Focus", "count": 784},
                        ]
                    },
                },
            ],
        },
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_histogram.date": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_histogram.date=product",
            "--relative-range=1w",
            "--format=tab",
            "--leftover-count",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        histogram_date.product
        histogram_date\t--\tFenix\tFirefox\tFocus\tMozillaVPN\tReferenceBrowser\tThunderbird\ttotal
        2022-06-24\t0\t49585\t62097\t938\t1\t1\t18202\t130824
        2022-06-25\t0\t49559\t60180\t907\t0\t0\t18888\t129534
        2022-06-26\t0\t48276\t59486\t871\t1\t0\t18532\t127166
        2022-06-27\t0\t49019\t55451\t957\t0\t0\t16913\t122340
        2022-06-28\t0\t49089\t41220\t931\t0\t0\t7858\t99098
        2022-06-29\t0\t50284\t38363\t895\t1\t0\t7040\t96583
        2022-06-30\t0\t49355\t62530\t784\t0\t0\t18934\t131603
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_table():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=table"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    # NOTE(willkg): this has spaces at the end of every line, so it's better to
    # encode it as a joined list of strings
    assert result.output == "\n".join(
        [
            "product",
            " product | count ",
            "---------|-------",
            " Firefox | 5     ",
            " Fenix   | 4     ",
            " total   | 19    ",
            "",
        ]
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_csv():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=csv"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product,count
        Firefox,5
        Fenix,4
        total,19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_markdown():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=markdown"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product
        product | count
        ------- | -----
        Firefox | 5
        Fenix | 4
        total | 19
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_json():
    supersearch_data = {
        "hits": [],
        "total": 19,
        "facets": {
            "product": [
                {"term": "Firefox", "count": 5},
                {"term": "Fenix", "count": 4},
            ]
        },
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-24", "<2022-07-01"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=json"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        {
          "product": [
            {
              "product": "Firefox",
              "count": 5
            },
            {
              "product": "Fenix",
              "count": 4
            },
            {
              "product": "total",
              "count": 19
            }
          ]
        }
        """
    )
