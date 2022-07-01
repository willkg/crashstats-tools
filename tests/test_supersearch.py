# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from textwrap import dedent

from click.testing import CliRunner

# from freezegun import freeze_time
import responses

from crashstats_tools import cmd_supersearch
from crashstats_tools.utils import DEFAULT_HOST


@responses.activate
def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch, args=["--help"], env={"COLUMNS": "100"}
    )
    assert result.exit_code == 0


@responses.activate
def test_no_args():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {"uuid": "ecf15793-caa9-4af8-94b5-90c810220624"},
            {"uuid": "ae692700-2230-411e-95d0-3feaf0220624"},
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": "uuid",
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        ecf15793-caa9-4af8-94b5-90c810220624
        ae692700-2230-411e-95d0-3feaf0220624
        """
    )


@responses.activate
def test_columns():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {
                "uuid": "ecf15793-caa9-4af8-94b5-90c810220624",
                "signature": "OOM | small",
            },
            {
                "uuid": "ae692700-2230-411e-95d0-3feaf0220624",
                "signature": "OOM | large",
            },
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": ["uuid", "signature"],
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=["--_columns=uuid", "--_columns=signature"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        ecf15793-caa9-4af8-94b5-90c810220624\tOOM | small
        ae692700-2230-411e-95d0-3feaf0220624\tOOM | large
        """
    )


@responses.activate
def test_host():
    host = "http://example.com"
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {"uuid": "ecf15793-caa9-4af8-94b5-90c810220624"},
            {"uuid": "ae692700-2230-411e-95d0-3feaf0220624"},
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        host + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": "uuid",
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=["--host=http://example.com"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        ecf15793-caa9-4af8-94b5-90c810220624
        ae692700-2230-411e-95d0-3feaf0220624
        """
    )


@responses.activate
def test_json():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {
                "uuid": "ecf15793-caa9-4af8-94b5-90c810220624",
                "signature": "OOM | small",
            },
            {
                "uuid": "ae692700-2230-411e-95d0-3feaf0220624",
                "signature": "OOM | large",
            },
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": ["uuid", "signature"],
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=["--_columns=uuid", "--_columns=signature", "--format=json"],
        env={"COLUMNS": "100"},
    )
    print(result.output)
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        [
          {
            "uuid": "ecf15793-caa9-4af8-94b5-90c810220624",
            "signature": "OOM | small"
          },
          {
            "uuid": "ae692700-2230-411e-95d0-3feaf0220624",
            "signature": "OOM | large"
          }
        ]
        """
    )


@responses.activate
def test_num():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {"uuid": "ecf15793-caa9-4af8-94b5-90c810220624"},
            {"uuid": "ae692700-2230-411e-95d0-3feaf0220624"},
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": "uuid",
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "2",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=["--num=2"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        ecf15793-caa9-4af8-94b5-90c810220624
        ae692700-2230-411e-95d0-3feaf0220624
        """
    )


@responses.activate
def test_headers():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {
                "uuid": "ecf15793-caa9-4af8-94b5-90c810220624",
                "signature": "OOM | small",
            },
            {
                "uuid": "ae692700-2230-411e-95d0-3feaf0220624",
                "signature": "OOM | large",
            },
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": ["uuid", "signature"],
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=["--headers", "--_columns=uuid", "--_columns=signature"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        uuid\tsignature
        ecf15793-caa9-4af8-94b5-90c810220624\tOOM | small
        ae692700-2230-411e-95d0-3feaf0220624\tOOM | large
        """
    )


@responses.activate
def test_supersearch_url():
    runner = CliRunner()
    supersearch_data = {
        "hits": [
            {
                "uuid": "ecf15793-caa9-4af8-94b5-90c810220624",
                "signature": "OOM | small",
            },
            {
                "uuid": "ae692700-2230-411e-95d0-3feaf0220624",
                "signature": "OOM | large",
            },
        ],
        "total": 2,
        "facets": {},
        "errors": [],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "_columns": ["uuid", "signature"],
                    "date": ">=2022-06-30",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            )
        ],
        status=200,
        json=supersearch_data,
    )

    result = runner.invoke(
        cli=cmd_supersearch.supersearch,
        args=[
            "--supersearch-url=https://crash-stats.mozilla.org"
            + "/api/SuperSearch/?"
            + "date=%3E%3D2022-06-30&"
            + "_columns=uuid&"
            + "_columns=signature"
        ],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        ecf15793-caa9-4af8-94b5-90c810220624\tOOM | small
        ae692700-2230-411e-95d0-3feaf0220624\tOOM | large
        """
    )
