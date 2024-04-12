# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hashlib
import json
import pathlib
from textwrap import dedent

from click.testing import CliRunner
import responses

from crashstats_tools import cmd_fetch_data
from crashstats_tools.utils import DEFAULT_HOST


@responses.activate
def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=["--help"],
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0


@responses.activate
def test_fetch_raw(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    raw_crash = {
        "ProductName": "Firefox",
        "Version": "100.0",
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/RawCrash/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            )
        ],
        status=200,
        json=raw_crash,
    )

    runner = CliRunner()
    args = ["--raw", "--no-dumps", "--no-processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        No API token provided. Set CRASHSTATS_API_TOKEN in the environment.
        Skipping dumps and protected data.
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching raw crash
        """
    )
    data = pathlib.Path(
        tmpdir / "raw_crash" / f"20{crash_id[-6:]}" / crash_id
    ).read_bytes()
    assert json.loads(data) == raw_crash


@responses.activate
def test_fetch_raw_with_token(tmpdir):
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    raw_crash = {
        "ProductName": "Firefox",
        "Version": "100.0",
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/RawCrash/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            ),
        ],
        status=200,
        json=raw_crash,
    )

    runner = CliRunner()
    args = ["--raw", "--no-dumps", "--no-processed", str(tmpdir), crash_id]

    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching raw crash
        """
    )
    data = pathlib.Path(
        tmpdir / "raw_crash" / f"20{crash_id[-6:]}" / crash_id
    ).read_bytes()
    assert json.loads(data) == raw_crash


@responses.activate
def test_fetch_dumps_no_token(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"

    runner = CliRunner()
    args = ["--raw", "--dumps", "--no-processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 2
    assert result.output == dedent(
        """\
        No API token provided. Set CRASHSTATS_API_TOKEN in the environment.
        Skipping dumps and protected data.
        Usage: fetch-data [OPTIONS] OUTPUTDIR [CRASH_IDS]...
        Try 'fetch-data --help' for help.

        Error: You cannot fetch dumps without providing an API token.
        """
    )


@responses.activate
def test_fetch_dumps_no_raw(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    api_token = "935e136cdfe14b83abae0e0cd97b634f"

    runner = CliRunner()
    args = ["--no-raw", "--dumps", "--no-processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 2
    assert result.output == dedent(
        """\
        Usage: fetch-data [OPTIONS] OUTPUTDIR [CRASH_IDS]...
        Try 'fetch-data --help' for help.

        Error: You cannot fetch dumps without also fetching the raw crash.
        """
    )


@responses.activate
def test_fetch_dumps(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    minidump = b"abcde"
    minidump_checksum = hashlib.sha256(minidump).hexdigest()
    api_token = "935e136cdfe14b83abae0e0cd97b634f"

    raw_crash = {
        "ProductName": "Firefox",
        "Version": "100.0",
        "metadata": {
            "dump_checksums": {
                "upload_file_minidump": minidump_checksum,
            },
        },
    }

    # Mock requests to return a raw crash data
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/RawCrash/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            ),
        ],
        status=200,
        json=raw_crash,
    )

    # Mock requests to return minidump
    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/RawCrash/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "raw",
                    "name": "dump",
                }
            ),
        ],
        status=200,
        body=minidump,
    )

    runner = CliRunner()
    args = ["--raw", "--dumps", "--no-processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching raw crash
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching dump: upload_file_minidump
        """
    )
    data = pathlib.Path(
        tmpdir / "raw_crash" / f"20{crash_id[-6:]}" / crash_id
    ).read_bytes()
    assert json.loads(data) == raw_crash

    data = pathlib.Path(tmpdir / "upload_file_minidump" / crash_id).read_bytes()
    assert data == minidump


@responses.activate
def test_fetch_processed(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    processed_crash = {
        "product": "Firefox",
        "version": "100.0",
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/ProcessedCrash/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            )
        ],
        status=200,
        json=processed_crash,
    )

    runner = CliRunner()
    args = ["--no-raw", "--no-dumps", "--processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        No API token provided. Set CRASHSTATS_API_TOKEN in the environment.
        Skipping dumps and protected data.
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching processed crash
        """
    )
    data = pathlib.Path(tmpdir / "processed_crash" / crash_id).read_bytes()
    assert json.loads(data) == processed_crash


@responses.activate
def test_fetch_processed_with_token(tmpdir):
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    api_token = "935e136cdfe14b83abae0e0cd97b634f"
    processed_crash = {
        "product": "Firefox",
        "version": "100.0",
    }

    responses.add(
        responses.GET,
        DEFAULT_HOST + "/api/ProcessedCrash/",
        match=[
            responses.matchers.header_matcher({"Auth-Token": api_token}),
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            ),
        ],
        status=200,
        json=processed_crash,
    )

    runner = CliRunner()
    args = ["--no-raw", "--no-dumps", "--processed", str(tmpdir), crash_id]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={
            "CRASHSTATS_API_TOKEN": api_token,
            "COLUMNS": "100",
        },
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        Using API token: 935exxxxxxxxxxxxxxxxxxxxxxxxxxxx
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching processed crash
        """
    )
    data = pathlib.Path(tmpdir / "processed_crash" / crash_id).read_bytes()
    assert json.loads(data) == processed_crash


@responses.activate
def test_host(tmpdir):
    host = "http://example.com"
    crash_id = "2ac9a763-83d2-4dca-89bb-091bd0220630"
    raw_crash = {
        "ProductName": "Firefox",
        "Version": "100.0",
    }

    responses.add(
        responses.GET,
        host + "/api/RawCrash/",
        match=[
            responses.matchers.query_param_matcher(
                {
                    "crash_id": crash_id,
                    "format": "meta",
                }
            )
        ],
        status=200,
        json=raw_crash,
    )

    runner = CliRunner()
    args = [
        "--host=" + host,
        "--raw",
        "--no-dumps",
        "--no-processed",
        str(tmpdir),
        crash_id,
    ]
    result = runner.invoke(
        cli=cmd_fetch_data.fetch_data,
        args=args,
        env={"COLUMNS": "100"},
    )
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        No API token provided. Set CRASHSTATS_API_TOKEN in the environment.
        Skipping dumps and protected data.
        2ac9a763-83d2-4dca-89bb-091bd0220630: fetching raw crash
        """
    )
    data = pathlib.Path(
        tmpdir / "raw_crash" / f"20{crash_id[-6:]}" / crash_id
    ).read_bytes()
    assert json.loads(data) == raw_crash
