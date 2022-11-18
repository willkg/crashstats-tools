# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import sys

import click
from rich.console import Console

from crashstats_tools.utils import DEFAULT_HOST, http_get, JsonDTEncoder, parse_crashid


def create_dir_if_needed(d):
    if not os.path.exists(d):
        os.makedirs(d)


def fetch_crash(
    console,
    host,
    fetchraw,
    fetchdumps,
    fetchprocessed,
    outputdir,
    api_token,
    crash_id,
    overwrite,
):
    """Fetch crash data and save to correct place on the file system

    https://antenna.readthedocs.io/en/latest/overview.html#aws-s3-file-hierarchy

    """
    if fetchraw:
        # Fetch raw crash metadata to OUTPUTDIR/raw_crash/DATE/CRASHID
        fn = os.path.join(outputdir, "raw_crash", "20" + crash_id[-6:], crash_id)
        if os.path.exists(fn) and not overwrite:
            console.print(
                f"[bold green]Fetching raw {crash_id}[/bold green] ... already exists"
            )
        else:
            console.print(f"[bold green]Fetching raw {crash_id}[/bold green]")
            resp = http_get(
                url=host + "/api/RawCrash/",
                params={"crash_id": crash_id, "format": "meta"},
                api_token=api_token,
            )

            # Save raw crash to file system
            raw_crash = resp.json()
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
                        f"[bold green]Fetching dump {crash_id}/{dump_name}[/bold green] ... "
                        + "already exists"
                    )
                else:
                    console.print(
                        f"[bold green]Fetching dump {crash_id}/{dump_name}[/bold green]"
                    )
                    resp = http_get(
                        url=host + "/api/RawCrash/",
                        params={
                            "crash_id": crash_id,
                            "format": "raw",
                            "name": file_name,
                        },
                        api_token=api_token,
                    )

                    if resp.status_code != 200:
                        raise Exception(
                            f"Something unexpected happened. status_code {resp.status_code}, "
                            + f"content {resp.content}"
                        )

                    create_dir_if_needed(os.path.dirname(fn))
                    with open(fn, "wb") as fp:
                        fp.write(resp.content)

    if fetchprocessed:
        # Fetch processed crash data
        fn = os.path.join(outputdir, "processed_crash", crash_id)
        if os.path.exists(fn) and not overwrite:
            console.print(
                f"[bold green]Fetching processed {crash_id}[/bold green] ... "
                + "already exists"
            )
        else:
            console.print(f"[bold green]Fetching processed {crash_id}[/bold green]")
            resp = http_get(
                host + "/api/ProcessedCrash/",
                params={"crash_id": crash_id, "format": "meta"},
                api_token=api_token,
            )

            # Save processed crash to file system
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
    "--color/--no-color",
    default=True,
    help=(
        "whether or not to colorize output; note that color is shut off "
        "when stdout is not an interactive terminal automatically"
    ),
)
@click.argument("outputdir")
@click.argument("crashids", nargs=-1)
@click.pass_context
def fetch_data(
    ctx,
    host,
    overwrite,
    fetchraw,
    fetchdumps,
    fetchprocessed,
    color,
    outputdir,
    crashids,
):
    """
    Fetches crash data from Crash Stats (https://crash-stats.mozilla.org/) system.

    Given one or more crash ids via command line or stdin (one per line), fetches
    crash data and puts it in specified directory.

    Crash data is split up into directories: raw_crash/, dump_names/,
    processed_crash/, and directories with the same name as the dump type.

    https://antenna.readthedocs.io/en/latest/overview.html#aws-s3-file-hierarchy

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
    host = host.rstrip("/")

    if not color:
        console = Console(color_system=None)
    else:
        console = Console()

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
        console.print(f"Using api token: {masked_token}")
    else:
        console.print(
            "[yellow]No api token provided. Set CRASHSTATS_API_TOKEN in the "
            + "environment.[/yellow]"
        )
        console.print(
            "[yellow]Skipping dumps and personally identifiable "
            + "information.[/yellow]"
        )

    if fetchdumps and not api_token:
        raise click.BadOptionUsage(
            "fetchdumps",
            "You cannot fetch dumps without providing an API token.",
            ctx=ctx,
        )

    if not crashids and not sys.stdin.isatty():
        crashids = list(click.get_text_stream("stdin").readlines())

    for crashid in crashids:
        crashid = crashid.strip()

        try:
            crashid = parse_crashid(crashid).strip()
        except ValueError:
            console.print(f"[yellow]Crash id not recognized: {crashid}[/yellow]")
            continue

        console.print(f"[bold green]Working on {crashid}...[/bold green]")
        fetch_crash(
            console=console,
            host=host,
            fetchraw=fetchraw,
            fetchdumps=fetchdumps,
            fetchprocessed=fetchprocessed,
            outputdir=outputdir,
            api_token=api_token,
            crash_id=crashid,
            overwrite=overwrite,
        )
    console.print("[bold green]Done![/bold green]")


if __name__ == "__main__":
    fetch_data()
