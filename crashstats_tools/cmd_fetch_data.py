# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import sys

import click

from crashstats_tools.utils import DEFAULT_HOST, http_get, JsonDTEncoder, parse_crashid


def create_dir_if_needed(d):
    if not os.path.exists(d):
        os.makedirs(d)


def fetch_crash(
    host, fetchraw, fetchdumps, fetchprocessed, outputdir, api_token, crash_id
):
    """Fetch crash data and save to correct place on the file system

    http://antenna.readthedocs.io/en/latest/architecture.html#aws-s3-file-hierarchy

    """
    if fetchraw:
        # Fetch raw crash metadata
        click.echo("Fetching raw %s" % crash_id)
        resp = http_get(
            url=host + "/api/RawCrash/",
            params={"crash_id": crash_id, "format": "meta"},
            api_token=api_token,
        )

        # Save raw crash to file system
        raw_crash = resp.json()
        fn = os.path.join(outputdir, "raw_crash", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(raw_crash, fp, cls=JsonDTEncoder, indent=2, sort_keys=True)

    if fetchdumps:
        # Save dump_names to file system
        dump_names = raw_crash.get("dump_checksums", {}).keys()
        fn = os.path.join(outputdir, "dump_names", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(list(dump_names), fp)

        # Fetch dumps
        for dump_name in dump_names:
            click.echo("Fetching dump %s/%s" % (crash_id, dump_name))

            # We store "upload_file_minidump" as "dump", so we need to use that
            # name when requesting from the RawCrash api
            file_name = dump_name
            if file_name == "upload_file_minidump":
                file_name = "dump"

            resp = http_get(
                url=host + "/api/RawCrash/",
                params={"crash_id": crash_id, "format": "raw", "name": file_name},
                api_token=api_token,
            )

            if resp.status_code != 200:
                raise Exception(
                    "Something unexpected happened. status_code %s, content %s"
                    % (resp.status_code, resp.content)
                )

            fn = os.path.join(outputdir, dump_name, crash_id)
            create_dir_if_needed(os.path.dirname(fn))
            with open(fn, "wb") as fp:
                fp.write(resp.content)

    if fetchprocessed:
        # Fetch processed crash data
        click.echo("Fetching processed %s" % crash_id)
        resp = http_get(
            host + "/api/ProcessedCrash/",
            params={"crash_id": crash_id, "format": "meta"},
            api_token=api_token,
        )

        # Save processed crash to file system
        fn = os.path.join(outputdir, "processed_crash", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(resp.json(), fp, cls=JsonDTEncoder, indent=2, sort_keys=True)


@click.command()
@click.option(
    "--host",
    default=DEFAULT_HOST,
    help="host to pull crash data from; this needs to match CRASHSTATS_API_TOKEN value",
)
@click.option(
    "--raw/--no-raw",
    "fetchraw",
    default=True,
    help="whether or not to save raw crash data",
)
@click.option(
    "--dumps/--no-dumps",
    "fetchdumps",
    default=True,
    help="whether or not to save dumps",
)
@click.option(
    "--processed/--no-processed",
    "fetchprocessed",
    default=False,
    help="whether or not to save processed crash data",
)
@click.argument("outputdir")
@click.argument("crashids", nargs=-1)
@click.pass_context
def fetch_data(ctx, host, fetchraw, fetchdumps, fetchprocessed, outputdir, crashids):
    """
    Fetches crash data from Crash Stats (https://crash-stats.mozilla.org/) system.

    Given one or more crash ids via command line or stdin (one per line), fetches
    crash data and puts it in specified directory.

    Crash data is split up into directories: raw_crash/, dump_names/,
    processed_crash/, and directories with the same name as the dump type.

    This requires an API token in order to download dumps, personally identifiable
    information, and security-sensitive data. It also reduces rate-limiting.  Set
    the CRASHSTATS_API_TOKEN environment variable to your API token value:

        CRASHSTATS_API_TOKEN=xyz fetch-data crashdata ...

    To create an API token for Crash Stats, visit:

        https://crash-stats.mozilla.org/api/tokens/

    Remember to abide by the data access policy when using data from Crash Stats!
    The policy is specified here:

    https://crash-stats.mozilla.org/documentation/memory_dump_access/
    """

    if fetchdumps and not fetchraw:
        raise click.BadOptionUsage(
            "fetchdumps",
            "You cannot fetch dumps without also fetching the raw crash. Exiting.",
            ctx=ctx,
        )

    # Validate outputdir and exit if it doesn't exist or isn't a directory
    if os.path.exists(outputdir) and not os.path.isdir(outputdir):
        raise click.ClickException(
            "%s is not a directory. Please fix. Exiting." % outputdir
        )

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if api_token:
        click.echo(
            "Using api token: %s%s" % (api_token[:4], "x" * (len(api_token) - 4))
        )
    else:
        click.echo(
            "No api token provided. Skipping dumps and personally identifiable information."
        )

    if not crashids and not sys.stdin.isatty():
        crashids = list(click.get_text_stream("stdin").readlines())

    crashids = [parse_crashid(crashid.strip()) for crashid in crashids]
    for crashid in crashids:
        crashid = crashid.strip()

        click.echo("Working on %s..." % crashid)
        fetch_crash(
            host=host,
            fetchraw=fetchraw,
            fetchdumps=fetchdumps if api_token else False,
            fetchprocessed=fetchprocessed,
            outputdir=outputdir,
            api_token=api_token,
            crash_id=crashid,
        )
    click.echo("Done!")


if __name__ == "__main__":
    fetch_data()
