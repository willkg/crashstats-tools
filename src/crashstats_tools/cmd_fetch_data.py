# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import json
from multiprocessing import Pool
import os
import sys

import click
from rich.console import Console

from crashstats_tools.libcrashstats import (
    get_crash_annotations,
    get_dump,
    get_processed_crash,
)
from crashstats_tools.utils import (
    DEFAULT_HOST,
    JsonDTEncoder,
    parse_crash_id,
)


def create_dir_if_needed(d):
    if not os.path.exists(d):
        os.makedirs(d)


def fetch_crash(
    crash_id,
    host,
    api_token,
    fetchraw,
    fetchdumps,
    fetchprocessed,
    outputdir,
    color,
    overwrite,
):
    """Fetch crash data and save to correct place on the file system

    https://antenna.readthedocs.io/en/latest/overview.html#aws-s3-file-hierarchy

    """
    if not color:
        console = Console(color_system=None)
    else:
        console = Console()

    try:
        crash_id = parse_crash_id(crash_id).strip()
    except ValueError:
        console.print(f"[yellow]{crash_id}: not a valid crash id[/yellow]")
        return

    if fetchraw:
        # Fetch raw crash metadata to OUTPUTDIR/raw_crash/DATE/CRASHID
        fn = os.path.join(outputdir, "raw_crash", "20" + crash_id[-6:], crash_id)
        if os.path.exists(fn) and not overwrite:
            console.print(f"{crash_id}: fetching raw crash -- already exists")
        else:
            console.print(f"{crash_id}: fetching raw crash")
            raw_crash = get_crash_annotations(crash_id, host=host, api_token=api_token)

            # Save raw crash to file system
            create_dir_if_needed(os.path.dirname(fn))
            with open(fn, "w") as fp:
                json.dump(raw_crash, fp, cls=JsonDTEncoder, indent=2, sort_keys=True)

        if fetchdumps:
            # Save dump_names to file system
            dump_names = raw_crash.get("metadata", {}).get("dump_checksums", {}).keys()
            fn = os.path.join(outputdir, "dump_names", crash_id)
            create_dir_if_needed(os.path.dirname(fn))
            with open(fn, "w") as fp:
                json.dump(list(dump_names), fp)

            # Fetch dumps
            for dump_name in dump_names:
                # We store "upload_file_minidump" as "dump", so we need to use that
                # name when requesting from the RawCrash api
                file_name = dump_name
                if file_name == "upload_file_minidump":
                    file_name = "dump"

                fn = os.path.join(outputdir, dump_name, crash_id)
                if os.path.exists(fn) and not overwrite:
                    console.print(
                        f"{crash_id}: fetching dump: {dump_name} -- already exists"
                    )
                else:
                    console.print(f"{crash_id}: fetching dump: {dump_name}")
                    dump_content = get_dump(
                        crash_id, dump_name=file_name, api_token=api_token, host=host
                    )
                    create_dir_if_needed(os.path.dirname(fn))
                    with open(fn, "wb") as fp:
                        fp.write(dump_content)

    if fetchprocessed:
        # Fetch processed crash data
        fn = os.path.join(outputdir, "processed_crash", crash_id)
        if os.path.exists(fn) and not overwrite:
            console.print(f"{crash_id}: fetching processed crash -- already exists")
        else:
            console.print(f"{crash_id}: fetching processed crash")
            processed_crash = get_processed_crash(
                crash_id, api_token=api_token, host=host
            )

            # Save processed crash to file system
            create_dir_if_needed(os.path.dirname(fn))
            with open(fn, "w") as fp:
                json.dump(
                    processed_crash, fp, cls=JsonDTEncoder, indent=2, sort_keys=True
                )


@click.command(context_settings={"show_default": True})
@click.option(
    "--host",
    default=DEFAULT_HOST,
    help="host to pull crash data from; this needs to match CRASHSTATS_API_TOKEN value",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    help="whether or not to overwrite existing data",
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
    default=False,
    help="whether or not to save dumps",
)
@click.option(
    "--processed/--no-processed",
    "fetchprocessed",
    default=False,
    help="whether or not to save processed crash data",
)
@click.option(
    "--workers",
    default=1,
    type=click.IntRange(1, 10, clamp=True),
    help="how many workers to use to download data; requires CRASHSTATS_API_TOKEN",
)
@click.option(
    "--color/--no-color",
    default=True,
    help=(
        "whether or not to colorize output; note that color is shut off "
        "when stdout is not an interactive terminal automatically"
    ),
)
@click.argument("outputdir")
@click.argument("crash_ids", nargs=-1)
@click.pass_context
def fetch_data(
    ctx,
    host,
    overwrite,
    fetchraw,
    fetchdumps,
    fetchprocessed,
    workers,
    color,
    outputdir,
    crash_ids,
):
    """
    Fetches crash data from Crash Stats (https://crash-stats.mozilla.org/) system.

    Given one or more crash ids via command line or stdin (one per line), fetches
    crash data and puts it in specified directory.

    Crash data is split up into directories: raw_crash/, dump_names/,
    processed_crash/, and directories with the same name as the dump type.

    https://antenna.readthedocs.io/en/latest/overview.html#aws-s3-file-hierarchy

    This requires an API token in order to download dumps and protected data.
    Using an API token also reduces rate-limiting. Set the CRASHSTATS_API_TOKEN
    environment variable to your API token value:

    CRASHSTATS_API_TOKEN=xyz fetch-data crashdata ...

    To create an API token for Crash Stats, visit:

    https://crash-stats.mozilla.org/api/tokens/

    Remember to abide by the data access policy when using data from Crash Stats!
    The policy is specified here:

    https://crash-stats.mozilla.org/documentation/protected_data_access/
    """
    if not color:
        console = Console(color_system=None)
    else:
        console = Console()

    host = host.rstrip("/")

    if fetchdumps and not fetchraw:
        raise click.BadOptionUsage(
            "fetchdumps",
            "You cannot fetch dumps without also fetching the raw crash.",
            ctx=ctx,
        )

    # Validate outputdir and exit if it doesn't exist or isn't a directory
    if os.path.exists(outputdir) and not os.path.isdir(outputdir):
        raise click.ClickException(f"{outputdir} is not a directory.")

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if api_token:
        masked_token = api_token[:4] + ("x" * (len(api_token) - 4))
        console.print(f"Using API token: {masked_token}")
    else:
        console.print(
            "[yellow]No API token provided. Set CRASHSTATS_API_TOKEN in the "
            + "environment.[/yellow]"
        )
        console.print("[yellow]Skipping dumps and protected data.[/yellow]")

    if workers > 1:
        if not api_token:
            raise click.BadOptionUsage(
                "workers",
                "You must specify a CRASHSTATS_API_TOKEN in order to set workers > 1.",
                ctx=ctx,
            )
        console.print(f"Using {workers} workers.")

    if fetchdumps and not api_token:
        raise click.BadOptionUsage(
            "fetchdumps",
            "You cannot fetch dumps without providing an API token.",
            ctx=ctx,
        )

    if not crash_ids and not sys.stdin.isatty():
        crash_ids = list(click.get_text_stream("stdin").readlines())

    fetch_crash_partial = partial(
        fetch_crash,
        host=host,
        api_token=api_token,
        fetchraw=fetchraw,
        fetchdumps=fetchdumps,
        fetchprocessed=fetchprocessed,
        color=color,
        outputdir=outputdir,
        overwrite=overwrite,
    )

    if workers > 1:
        with Pool(workers) as p:
            p.map(fetch_crash_partial, crash_ids)

    else:
        for crash_id in crash_ids:
            fetch_crash_partial(crash_id)


if __name__ == "__main__":
    fetch_data()
