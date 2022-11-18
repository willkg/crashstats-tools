# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time

import click
from rich.console import Console
from more_itertools import chunked

from crashstats_tools.utils import DEFAULT_HOST, http_post, parse_crashid


CHUNK_SIZE = 50
SLEEP_DEFAULT = 1


@click.command()
@click.option(
    "--host",
    default=DEFAULT_HOST,
    show_default=True,
    help="host for system to reprocess in",
)
@click.option(
    "--sleep",
    type=int,
    default=SLEEP_DEFAULT,
    show_default=True,
    help="how long in seconds to sleep before submitting the next group",
)
@click.option(
    "--ruleset",
    default="",
    show_default=True,
    help="processor pipeline ruleset to use for reprocessing these crash ids",
)
@click.option(
    "--allow-many/--no-allow-many",
    default=False,
    help=(
        "don't prompt user about letting us know about reprocessing "
        "more than 10,000 crashes"
    ),
)
@click.option(
    "--color/--no-color",
    default=True,
    help=(
        "whether or not to colorize output; note that color is shut off "
        "when stdout is not an interactive terminal automatically"
    ),
)
@click.argument("crashids", nargs=-1)
@click.pass_context
def reprocess(ctx, host, sleep, ruleset, allow_many, color, crashids):
    """
    Sends specified crashes for reprocessing

    This requires CRASHSTATS_API_TOKEN to be set in the environment to a valid
    API token.

    To create an API token for Crash Stats, visit:

    https://crash-stats.mozilla.org/api/tokens/

    Note: If you're processing more than 10,000 crashes, you should use a sleep
    value that balances the rate of crash ids being added to the queue and the
    rate of crash ids being processed. For example, you could use "--sleep 10"
    which will sleep for 10 seconds between submitting groups of crashes.

    Also, if you're processing a lot of crashes, you should let us know before
    you do it.
    """
    host = host.rstrip("/")

    if not color:
        console = Console(color_system=None)
        error_console = Console(stderr=True, color_system=None)
    else:
        console = Console()
        error_console = Console(stderr=True)

    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if not api_token:
        error_console.print(
            "[yellow]No api token provided. Set CRASHSTATS_API_TOKEN in the "
            + "environment.[/yellow]"
        )
        ctx.exit(1)

    masked_token = api_token[:4] + ("x" * (len(api_token) - 4))
    console.print(f"Using api token: {masked_token}")

    url = host.rstrip("/") + "/api/Reprocessing/"
    console.print(f"[bold green]Sending reprocessing requests to: {url}[/bold green]")

    if not crashids and not sys.stdin.isatty():
        crashids = list(click.get_text_stream("stdin").readlines())

    to_process = []
    for crashid in crashids:
        crashid = crashid.strip()
        try:
            crashid = parse_crashid(crashid).strip()
        except ValueError:
            console.print(f"[yellow]Crash id not recognized: {crashid}[/yellow]")
            continue

        to_process.append(crashid)

    if not to_process:
        raise click.BadParameter(
            message="No crashids specified.",
            ctx=ctx,
            param="crashids",
            param_hint="crashids",
        )

    console.print(
        f"[bold green]Reprocessing {len(to_process)} crashes sleeping {sleep} "
        + "seconds between groups...[/bold green]"
    )

    if len(to_process) > 10000 and not allow_many:
        console.print(
            "[yellow]You are trying to reprocess more than 10,000 crash reports "
            + "at once.[/yellow]"
        )
        console.print(
            "[yellow]Please let us know on #crashreporting on Matrix before you "
            + "do this.[/yellow]"
        )
        console.print("")
        console.print("[yellow]Use --allow-many argument to reprocess.[/yellow]")
        ctx.exit(1)

    groups = list(chunked(to_process, CHUNK_SIZE))
    for i, group in enumerate(groups):
        if i > 0:
            # NOTE(willkg): We sleep here because the webapp has a bunch of rate
            # limiting and we don't want to trigger that. It'd be nice if we didn't
            # have to do this.
            time.sleep(sleep)

        last_crashid = group[-1]
        this_group = i + 1
        total_groups = len(groups)
        console.print(
            f"Processing group ending with {last_crashid} ... "
            + f"({this_group}/{total_groups})"
        )

        if ruleset:
            group = [f"{crashid}:{ruleset}" for crashid in group]

        resp = http_post(url, data={"crash_ids": group}, api_token=api_token)
        if resp.status_code != 200:
            console.print(
                "[yellow]Got back non-200 status code: "
                + f"{resp.status_code} {resp.content}[/yellow]"
            )
            continue

    console.print("[bold green]Done![/bold green]")


if __name__ == "__main__":
    reprocess()
