# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
from urllib.parse import urlparse, parse_qs

import click
from rich.console import Console
from rich.table import Table

from crashstats_tools.utils import (
    escape_whitespace,
    DEFAULT_HOST,
    http_get,
    INFINITY,
    MissingField,
    parse_args,
    tableize_markdown,
    tableize_tab,
)


MAX_PAGE = 1000


def fetch_supersearch(
    console, host, params, num_results, api_token=None, verbose=False
):
    """Generator that returns Super Search results

    :arg str host: the host to query
    :arg dict params: dict of super search parameters to base the query on
    :arg varies num: number of results to get or INFINITY
    :arg str api_token: the API token to use or None
    :arg bool verbose: whether or not to print verbose things

    :returns: generator of crash ids

    """
    url = host + "/api/SuperSearch/"

    # Set up first page
    params["_results_offset"] = 0
    params["_results_number"] = min(MAX_PAGE, num_results)

    # Fetch pages of crash ids until we've gotten as many as we want or there
    # aren't any more to get
    crashids_count = 0
    while True:
        if verbose:
            console.print(url, params)

        resp = http_get(url=url, params=params, api_token=api_token)
        hits = resp.json()["hits"]

        for hit in hits:
            crashids_count += 1
            yield hit

            # If we've gotten as many crashids as we need, we return
            if crashids_count >= num_results:
                return

        # If there are no more crash ids to get, we return
        total = resp.json()["total"]
        if not hits or crashids_count >= total:
            return

        # Get the next page, but only as many results as we need
        params["_results_offset"] += MAX_PAGE
        params["_results_number"] = min(
            # MAX_PAGE is the maximum we can request
            MAX_PAGE,
            # The number of results Super Search can return to us that is
            # hasn't returned so far
            total - crashids_count,
            # The numver of results we want that we haven't gotten, yet
            num_results - crashids_count,
        )


def extract_supersearch_params(url):
    """Parses out params from the query string and drops any aggs-related ones."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Remove any aggs
    aggs_keys = ("_facets", "_aggs", "_histogram", "_cardinality")
    for key in list(params.keys()):
        if key.startswith(aggs_keys):
            del params[key]

    return params


@click.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
@click.option(
    "--host",
    default=DEFAULT_HOST,
    show_default=True,
    help="host for system to fetch crashids from",
)
@click.option("--supersearch-url", default="", help="Super Search url to base query on")
@click.option(
    "--num",
    default=100,
    show_default=True,
    type=click.UNPROCESSED,
    help='number of crash ids you want or "all" for all of them',
)
@click.option(
    "--headers/--no-headers",
    default=False,
    show_default=True,
    help="whether or not to show table headers",
)
@click.option(
    "--format",
    "format_type",
    default="tab",
    show_default=True,
    type=click.Choice(["table", "tab", "json", "markdown"], case_sensitive=False),
    help="format to print output",
)
@click.option(
    "--verbose/--no-verbose", default=False, help="whether to print debugging output"
)
@click.option(
    "--color/--no-color",
    default=True,
    help=(
        "whether or not to colorize output; note that color is shut off "
        "when stdout is not an interactive terminal automatically"
    ),
)
@click.pass_context
def supersearch(ctx, host, supersearch_url, num, headers, format_type, verbose, color):
    """
    Fetches data from Crash Stats using Super Search

    There are two ways to run this:

    First, you can specify Super Search API fields to generate the query.

    For example:

    $ supersearch --product=Firefox --num=100 --date='>=2019-07-31'

    Second, you can pass in a url from a Super Search on Crash Stats. This command
    will then pull out the parameters. You can override those parameters with
    command line arguments.

    $ supersearch --supersearch-url='longurlhere' --num=100

    Make sure to use single quotes when specifying values so that your shell doesn't
    expand variables.

    Returned fields are tab-delimited. You can specify them using the Super Search
    field "_columns".

    For example:

    $ supersearch --_columns=uuid --_columns=product --_columns=build_id --_columns=version

    Results are tab-delimited. Tabs and newlines in output is escaped.

    This doesn't support any of the aggregations at this time.

    For list of available fields and Super Search API documentation, see:

    https://crash-stats.mozilla.org/documentation/supersearch/

    https://crash-stats.mozilla.org/documentation/supersearch/api/

    This requires an API token in order to download search and download personally
    identifiable information and security-sensitive data. It also reduces
    rate-limiting. Set the CRASHSTATS_API_TOKEN environment variable to your API
    token value:

    CRASHSTATS_API_TOKEN=xyz supersearch ...

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

    if verbose:
        # Set logging to DEBUG because this picks up debug logging from
        # requests which lets us see urls.
        logging.basicConfig(level=logging.DEBUG)

    # Start with params from --url value or product=Firefox
    if supersearch_url:
        params = extract_supersearch_params(supersearch_url)
    else:
        params = {}

    params.update(parse_args(ctx.args))

    params["_facets_size"] = 0

    if "_columns" not in params:
        params["_columns"] = ["uuid"]

    if "_sort" not in params and "date" not in params:
        # If _sort and date aren't in params, then we're going to assume the
        # user wants the most recent crash reports.
        params["_sort"] = ["-date"]

    num_results = num
    if num_results == "all":
        num_results = INFINITY

    else:
        try:
            num_results = int(num_results)
        except ValueError:
            raise click.BadOptionUsage(
                "num", 'num needs to be an integer or "all"', ctx=ctx
            )

    if verbose:
        console.print(f"Params: {params}")

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if verbose:
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

    hits = fetch_supersearch(
        console=console,
        host=host,
        params=params,
        num_results=num_results,
        api_token=api_token,
        verbose=verbose,
    )

    if format_type == "table":
        table = Table(show_edge=False, show_header=headers)
        for column in params["_columns"]:
            table.add_column(column, justify="left")

        for hit_i, hit in enumerate(hits):
            if hit_i == 0:
                for field in params["_columns"]:
                    if field not in hit:
                        raise click.UsageError(f"{field}: no data")

            table.add_row(
                *[escape_whitespace(hit[field]) for field in params["_columns"]]
            )

        console.print(table)

    elif format_type == "tab":
        try:
            for line in tableize_tab(
                params["_columns"], data=hits, show_headers=headers
            ):
                # NOTE(willkg): we don't use console.print here because rich will do fancy
                # things like wrapping and fixing tabs we don't want that
                click.echo(line)
        except MissingField as exc:
            raise click.UsageError(f"{exc.args[0]}: no data")

    elif format_type == "markdown":
        try:
            for line in tableize_markdown(params["_columns"], data=hits):
                # NOTE(willkg): we don't use console.print here because rich will do fancy
                # things like wrapping and fixing tabs we don't want that
                click.echo(line)
        except MissingField as exc:
            raise click.UsageError(f"{exc.args[0]}: no data")

    elif format_type == "json":
        records = []
        for hit_i, hit in enumerate(hits):
            if hit_i == 0:
                for field in params["_columns"]:
                    if field not in hit:
                        raise click.UsageError(f"{field}: no data")

            records.append(
                {
                    field: escape_whitespace(hit.get(field, "<no data>"))
                    for field in params["_columns"]
                }
            )
        console.print_json(json.dumps(records))


if __name__ == "__main__":
    supersearch()
