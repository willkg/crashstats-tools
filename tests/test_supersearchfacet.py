# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from textwrap import dedent

from click.testing import CliRunner
import freezegun
import responses

from crashstats_tools import cmd_supersearchfacet
from crashstats_tools.utils import DEFAULT_HOST


def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--help"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_basic():
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
        args=["--_facets=product", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
        """
    )


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
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--host=" + host, "--_facets=product", "--format=tab"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
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
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=tab"],
        env={"CRASHSTATS_API_TOKEN": api_token, "COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
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
    runner = CliRunner()
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
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
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
    runner = CliRunner()
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
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
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
    runner = CliRunner()
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
        product\tcount
        Firefox\t5
        Fenix\t4
        --\t10
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
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=markdown"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        product | count
        ------- | -----
        Firefox | 5
        Fenix | 4
        -- | 10
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
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=["--_facets=product", "--format=json"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        [
          {
            "product": "Firefox",
            "count": 5
          },
          {
            "product": "Fenix",
            "count": 4
          },
          {
            "product": "--",
            "count": 10
          }
        ]
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_period_daily():
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-07-01 00:00:00", "<2022-07-02 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 22,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 7},
                    {"term": "Fenix", "count": 3},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-30 00:00:00", "<2022-07-01 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 19,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 6},
                    {"term": "Fenix", "count": 3},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-29 00:00:00", "<2022-06-30 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 18,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 4},
                    {"term": "Fenix", "count": 4},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-28 00:00:00", "<2022-06-29 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 19,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 5},
                    {"term": "Fenix", "count": 4},
                ]
            },
            "errors": [],
        },
    )

    runner = CliRunner()

    # Test format=tab
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=tab",
            "--start-date=2022-06-28",
            "--end-date=2022-07-01",
            "--period=daily",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        date\t--\tFenix\tFirefox
        2022-06-28 00:00:00\t10\t4\t5
        2022-06-29 00:00:00\t10\t4\t4
        2022-06-30 00:00:00\t10\t3\t6
        2022-07-01 00:00:00\t12\t3\t7
        """
    )

    # Test format=markdown
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=markdown",
            "--start-date=2022-06-28",
            "--end-date=2022-07-01",
            "--period=daily",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        date | -- | Fenix | Firefox
        ---- | -- | ----- | -------
        2022-06-28 00:00:00 | 10 | 4 | 5
        2022-06-29 00:00:00 | 10 | 4 | 4
        2022-06-30 00:00:00 | 10 | 3 | 6
        2022-07-01 00:00:00 | 12 | 3 | 7
        """
    )

    # Test format=json
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=json",
            "--start-date=2022-06-28",
            "--end-date=2022-07-01",
            "--period=daily",
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        [
          {
            "date": "2022-06-28 00:00:00",
            "--": 10,
            "Fenix": 4,
            "Firefox": 5
          },
          {
            "date": "2022-06-29 00:00:00",
            "--": 10,
            "Fenix": 4,
            "Firefox": 4
          },
          {
            "date": "2022-06-30 00:00:00",
            "--": 10,
            "Fenix": 3,
            "Firefox": 6
          },
          {
            "date": "2022-07-01 00:00:00",
            "--": 12,
            "Fenix": 3,
            "Firefox": 7
          }
        ]
        """
    )


@freezegun.freeze_time("2022-07-01 12:00:00")
@responses.activate
def test_period_weekly():
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-01 00:00:00", "<2022-06-08 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 22,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 7},
                    {"term": "Fenix", "count": 3},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-08 00:00:00", "<2022-06-15 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 19,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 6},
                    {"term": "Fenix", "count": 3},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-15 00:00:00", "<2022-06-22 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 18,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 4},
                    {"term": "Fenix", "count": 4},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-22 00:00:00", "<2022-06-29 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 19,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 5},
                    {"term": "Fenix", "count": 4},
                ]
            },
            "errors": [],
        },
    )
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_facets": "product",
                    "date": [">=2022-06-29 00:00:00", "<2022-07-06 00:00:00"],
                    "_results_number": "0",
                }
            ),
        ],
        status=200,
        json={
            "hits": [],
            "total": 19,
            "facets": {
                "product": [
                    {"term": "Firefox", "count": 5},
                    {"term": "Fenix", "count": 4},
                ]
            },
            "errors": [],
        },
    )

    runner = CliRunner()

    # Test format=tab
    result = runner.invoke(
        cli=cmd_supersearchfacet.supersearchfacet,
        args=[
            "--_facets=product",
            "--format=tab",
            "--start-date=2022-06-01",
            "--end-date=2022-07-01",
            "--period=weekly",
        ],
        env={"COLUMNS": "100"},
    )
    print(result.output)
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        date\t--\tFenix\tFirefox
        2022-06-01 00:00:00\t12\t3\t7
        2022-06-08 00:00:00\t10\t3\t6
        2022-06-15 00:00:00\t10\t4\t4
        2022-06-22 00:00:00\t10\t4\t5
        2022-06-29 00:00:00\t10\t4\t5
        """
    )
