# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from textwrap import dedent
from unittest import mock
import uuid

from click.testing import CliRunner
import responses

from crashstats_tools import cmd_reprocess
from crashstats_tools.utils import DEFAULT_HOST


@responses.activate
def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=["--help"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0


@responses.activate
def test_no_token():
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=[crash_id],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 1
    assert result.output == dedent(
        """\
        No API token provided. Set CRASHSTATS_API_TOKEN in the environment.
        """
    )


@responses.activate
def test_reprocess_from_args():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"

    # Mock requests to return araw crash data
    responses.add(
        responses.POST,
        DEFAULT_HOST + "/api/Reprocessing/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.urlencoded_params_matcher({"crash_ids": crash_id}),
        ],
        status=200,
        # FIXME(willkg): it might be nice to return the correct response body
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=[crash_id],
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: https://crash-stats.mozilla.org/api/Reprocessing/
        Reprocessing 1 crashes sleeping 1 seconds between groups...
        Rough estimate: 0:00:00
        Processing group ending with 2ac9a763-83d2-4dca-89bb-091bd0220630 ... (1/1)
        Done!
        """
    )


@responses.activate
def test_reprocess_from_stdin():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"

    # Mock requests to return araw crash data
    responses.add(
        responses.POST,
        DEFAULT_HOST + "/api/Reprocessing/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.urlencoded_params_matcher({"crash_ids": crash_id}),
        ],
        status=200,
        # FIXME(willkg): it might be nice to return the correct response body
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=[],
        input=crash_id + "\n",
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: https://crash-stats.mozilla.org/api/Reprocessing/
        Reprocessing 1 crashes sleeping 1 seconds between groups...
        Rough estimate: 0:00:00
        Processing group ending with 2ac9a763-83d2-4dca-89bb-091bd0220630 ... (1/1)
        Done!
        """
    )


@responses.activate
def test_reprocess_with_ruleset():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"

    # Mock requests to return araw crash data
    responses.add(
        responses.POST,
        DEFAULT_HOST + "/api/Reprocessing/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.urlencoded_params_matcher(
                {"crash_ids": crash_id + ":signature"}
            ),
        ],
        status=200,
        # FIXME(willkg): it might be nice to return the correct response body
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=["--ruleset=signature", crash_id],
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: https://crash-stats.mozilla.org/api/Reprocessing/
        Reprocessing 1 crashes sleeping 1 seconds between groups...
        Rough estimate: 0:00:00
        Processing group ending with 2ac9a763-83d2-4dca-89bb-091bd0220630 ... (1/1)
        Done!
        """
    )


@responses.activate
def test_reprocess_host():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    host = "http://example.com"

    # Mock requests to return araw crash data
    responses.add(
        responses.POST,
        host + "/api/Reprocessing/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.urlencoded_params_matcher({"crash_ids": crash_id}),
        ],
        status=200,
        # FIXME(willkg): it might be nice to return the correct response body
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=["--host=" + host, crash_id],
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: http://example.com/api/Reprocessing/
        Reprocessing 1 crashes sleeping 1 seconds between groups...
        Rough estimate: 0:00:00
        Processing group ending with 2ac9a763-83d2-4dca-89bb-091bd0220630 ... (1/1)
        Done!
        """
    )


def create_new_ooid():
    """Create a new crash id"""
    datestamp = datetime.date.today()
    new_uuid = str(uuid.uuid4())
    return "%s%02d%02d%02d" % (
        new_uuid[:-6],
        datestamp.year % 100,
        datestamp.month,
        datestamp.day,
    )


@responses.activate
def test_reprocess_tenthousand():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_ids = [create_new_ooid() for i in range(10_010)]

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        input="\n".join(crash_ids) + "\n",
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 1
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: https://crash-stats.mozilla.org/api/Reprocessing/
        Reprocessing 10,010 crashes sleeping 1 seconds between groups...
        Rough estimate: 0:05:00
        You are trying to reprocess more than 10,000 crash reports at once.
        Please let us know on #crashreporting on Matrix before you do this.

        Use --allow-many argument to reprocess.
        """
    )


@responses.activate
def test_reprocess_tenthousand_allowmany():
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_ids = [create_new_ooid() for i in range(10_010)]

    # Mock requests to return araw crash data
    responses.add(
        responses.POST,
        DEFAULT_HOST + "/api/Reprocessing/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.urlencoded_params_matcher({"crash_ids": mock.ANY}),
        ],
        status=200,
        # FIXME(willkg): it might be nice to return the correct response body
    )

    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_reprocess.reprocess,
        args=["--allow-many", "--sleep=0"],
        input="\n".join(crash_ids) + "\n",
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output.startswith(
        dedent(
            f"""\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        Sending reprocessing requests to: https://crash-stats.mozilla.org/api/Reprocessing/
        Reprocessing 10,010 crashes sleeping 0 seconds between groups...
        Rough estimate: 0:01:40
        Processing group ending with {crash_ids[49]} ... (1/201)
        Processing group ending with {crash_ids[99]} ... (2/201)
        """
        )
    )
    print(result.output.splitlines()[-3:])
    assert result.output.endswith(
        dedent(
            f"""\
        Processing group ending with {crash_ids[9_949]} ... (199/201) 0:00:00
        Processing group ending with {crash_ids[9_999]} ... (200/201) 0:00:00
        Processing group ending with {crash_ids[10_009]} ... (201/201) 0:00:00
        Done!
        """
        )
    )
