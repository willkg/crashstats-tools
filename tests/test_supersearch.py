# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from textwrap import dedent

from click.testing import CliRunner
import responses

from crashstats_tools import cmd_supersearch
from crashstats_tools.utils import DEFAULT_HOST


@responses.activate
def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli, args=["--help"], env={"COLUMNS": "100"}
    )
    assert result.exit_code == 0


@responses.activate
def test_no_args():
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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
def test_token():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
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
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "_columns": "uuid",
                    "_sort": "-date",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_data,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
        env={"CRASHSTATS_API_TOKEN": api_token, "COLUMNS": "100"},
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
        args=["--_columns=uuid", "--_columns=signature", "--format=json"],
        env={"COLUMNS": "100"},
    )
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
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


@responses.activate
def test_return_query():
    # This makes sure that passing in _retury_query=1 does the right thing by
    # calling the correct supersearch function.
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    supersearch_query_data = {
        "query": {
            "query": {
                "filtered": {
                    "query": {"match_all": {}},
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "bool": {
                                        "must": [
                                            {
                                                "range": {
                                                    "processed_crash.date_processed": {
                                                        "gte": "2024-08-06T13:56:15+00:00"
                                                    }
                                                }
                                            },
                                            {
                                                "range": {
                                                    "processed_crash.date_processed": {
                                                        "lte": "2024-08-13T13:56:15+00:00"
                                                    }
                                                }
                                            },
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                }
            },
            "sort": [{"processed_crash.date_processed": {"order": "desc"}}],
            "from": 0,
            "size": 100,
            "fields": ["processed_crash.uuid"],
        },
        "indices": ["socorro202432", "socorro202433"],
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/SuperSearch/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "_columns": "uuid",
                    "_sort": "-date",
                    "_return_query": "1",
                    "_results_offset": "0",
                    "_results_number": "100",
                    "_facets_size": "0",
                }
            ),
        ],
        status=200,
        json=supersearch_query_data,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_supersearch.supersearch_cli,
        args=["--_return_query=1"],
        env={"CRASHSTATS_API_TOKEN": api_token, "COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        {
            'query': {
                'query': {
                    'filtered': {
                        'query': {'match_all': {}},
                        'filter': {
                            'bool': {
                                'must': [
                                    {
                                        'bool': {
                                            'must': [
                                                {
                                                    'range': {
                                                        'processed_crash.date_processed': {
                                                            'gte': '2024-08-06T13:56:15+00:00'
                                                        }
                                                    }
                                                },
                                                {
                                                    'range': {
                                                        'processed_crash.date_processed': {
                                                            'lte': '2024-08-13T13:56:15+00:00'
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                'sort': [{'processed_crash.date_processed': {'order': 'desc'}}],
                'from': 0,
                'size': 100,
                'fields': ['processed_crash.uuid']
            },
            'indices': ['socorro202432', 'socorro202433']
        }
    """
    )
