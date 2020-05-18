# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time

import click
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
    "--allowmany/--no-allow-many",
    default=False,
    help=(
        "don't prompt user about letting us know about reprocessing "
        "more than 10,000 crashes"
    ),
)
@click.argument("crashids", nargs=-1)
@click.pass_context
def reprocess(ctx, host, sleep, allowmany, crashids):
    """
    Sends specified crashes for reprocessing

    This requires CRASHSTATS_API_TOKEN to be set in the environment to a valid
    API token.

    Note: If you're processing more than 10,000 crashes, you should use a sleep
    value that balances the rate of crash ids being added to the queue and the
    rate of crash ids being processed. For example, you could use "--sleep 10"
    which will sleep for 10 seconds between submitting groups of crashes.

    Also, if you're processing a lot of crashes, you should let us know before
    you do it.
    """
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if not api_token:
        click.echo("You need to set CRASHSTATS_API_TOKEN in the environment.")
        return 1

    url = host.rstrip("/") + "/api/Reprocessing/"
    click.echo("Sending reprocessing requests to: %s" % url)

    if not crashids and not sys.stdin.isatty():
        crashids = list(click.get_text_stream("stdin").readlines())

    crashids = [parse_crashid(crashid.strip()) for crashid in crashids]

    if not crashids:
        raise click.BadParameter(
            message="No crashids specified.",
            ctx=ctx,
            param="crashids",
            param_hint="crashids",
        )

    if len(crashids) > 10000 and not allowmany:
        click.echo(
            "You are trying to reprocess more than 10,000 crash reports at "
            "once. Please let us know on #breakpad on irc.mozilla.org "
            "before you do this."
        )
        click.echo("")
        click.echo("Pass in --allowmany argument.")
        click.echo("")
        click.echo("Exiting.")
        ctx.exit(1)

    click.echo(
        "Reprocessing %s crashes sleeping %s seconds between groups..."
        % (len(crashids), sleep)
    )

    groups = list(chunked(crashids, CHUNK_SIZE))
    for i, group in enumerate(groups):
        if i > 0:
            # NOTE(willkg): We sleep here because the webapp has a bunch of rate
            # limiting and we don't want to trigger that. It'd be nice if we didn't
            # have to do this.
            time.sleep(sleep)

        click.echo(
            "Processing group ending with %s ... (%s/%s)"
            % (group[-1], i + 1, len(groups))
        )
        resp = http_post(url, data={"crash_ids": group}, api_token=api_token)
        if resp.status_code != 200:
            click.echo(
                "Got back non-200 status code: %s %s" % (resp.status_code, resp.content)
            )
            continue

    click.echo("Done!")


if __name__ == "__main__":
    reprocess()
