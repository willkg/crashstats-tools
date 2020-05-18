# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import logging
import os
import re
from urllib.parse import urlparse, parse_qs

import click

from crashstats_tools.utils import (
    DEFAULT_HOST,
    http_get,
    parse_args,
    tableize_markdown,
    tableize_tab,
)


RELATIVE_RE = re.compile(r"(\d+)([hdwm])", re.IGNORECASE)

DEFAULT_NOW = datetime.datetime.now().strftime("%Y-%m-%d")


def now():
    return datetime.datetime.now()


def parse_relative_date(text):
    """Takes a relative date specification and returns a timedelta."""
    parsed = RELATIVE_RE.match(text)

    count = int(parsed.group(1))
    unit = parsed.group(2)

    unit_to_arg = {"h": "hours", "d": "days", "w": "weeks", "m": "months"}
    return datetime.timedelta(**{unit_to_arg[unit]: count})


def generate_dates(start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    while start_date <= end_date:
        next_end_date = start_date + datetime.timedelta(days=1)
        yield start_date.strftime("%Y-%m-%d"), next_end_date.strftime("%Y-%m-%d")
        start_date = next_end_date


def fetch_supersearch_facets(host, params, api_token=None, verbose=False):
    """Generator that returns Super Search results

    :arg str host: the host to query
    :arg dict params: dict of super search parameters to base the query on
    :arg str api_token: the API token to use or None
    :arg bool verbose: whether or not to print verbose things

    :returns: generator of crash ids

    """
    url = host + "/api/SuperSearch/"

    params["_results_number"] = 0

    if verbose:
        click.echo("%s %s" % (url, params))

    resp = http_get(url=url, params=params, api_token=api_token)
    return resp.json()["facets"]


def extract_supersearch_params(url):
    """Parses out params from the query string and drops any aggs-related ones."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    for key in list(params.keys()):
        # Remove any aggs
        aggs_keys = ("_facets", "_aggs", "_histogram", "_cardinality")
        if key.startswith(aggs_keys):
            del params[key]

    return params


@click.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
@click.option(
    "--host", default=DEFAULT_HOST, help="host for system to fetch facets from"
)
@click.option("--supersearch-url", default="", help="Super Search url to base query on")
@click.option(
    "--start-date", default="", help="start date for range; YYYY-MM-DD format"
)
@click.option(
    "--end-date",
    default=DEFAULT_NOW,
    show_default=True,
    help="end date for range; YYYY-MM-DD format",
)
@click.option(
    "--relative-range", default="7d", help="relative range ending on end-date"
)
@click.option(
    "--daily/--no-daily", default=False, help="poorly named argument to get count/day"
)
@click.option(
    "--format",
    "format_type",
    default="tab",
    show_default=True,
    type=click.Choice(["tab", "markdown", "json"], case_sensitive=False),
    help="format to print output",
)
@click.option(
    "--verbose/--no-verbose", default=False, help="whether to print debugging output"
)
@click.pass_context
def supersearchfacet(
    ctx,
    host,
    supersearch_url,
    end_date,
    start_date,
    relative_range,
    daily,
    format_type,
    verbose,
):
    """Fetches facet data from Crash Stats using Super Search

    There are two ways to run this:

    First, you can specify Super Search API fields to generate the query.

    For example:

    $ supersearchfacet --product=Firefox --_facets=version

    Second, you can pass in a url from a Super Search on Crash Stats. This command
    will then pull out the parameters. You can override those parameters with
    command line arguments.

    $ supersearchfacet --supersearch-url='longurlhere' --_facets=version

    Make sure to use single quotes when specifying values so that your shell doesn't
    expand variables.

    You need to specify at least one facet using "--_facets".

    By default, returned data is a tab-delimited table. Tabs and newlines in
    output is escaped. Use "--format" to specify a different output format.

    For list of available fields and Super Search API documentation, see:

    https://crash-stats.mozilla.org/documentation/supersearch/

    https://crash-stats.mozilla.org/documentation/supersearch/api/

    This generates a table values and counts. If you want values and counts
    over a series of days, use "--daily".

    This requires an API token in order to download search and download personally
    identifiable information and security-sensitive data. It also reduces
    rate-limiting.  Set the CRASHSTATS_API_TOKEN environment variable to your API
    token value:

    CRASHSTATS_API_TOKEN=xyz supersearchfacet ...

    To create an API token for Crash Stats, visit:

    https://crash-stats.mozilla.org/api/tokens/

    Remember to abide by the data access policy when using data from Crash Stats!
    The policy is specified here:

    https://crash-stats.mozilla.org/documentation/memory_dump_access/
    """

    # Require at least one facet specified.
    parsed_args = parse_args(ctx.args)
    if "_facets" not in parsed_args:
        click.echo(ctx.get_help())
        ctx.exit(1)

    if verbose:
        # Set logging to DEBUG because this picks up debug logging from
        # requests which lets us see urls.
        logging.basicConfig(level=logging.DEBUG)

    host = host.rstrip("/")

    # Start with params from --url value or product=Firefox
    if supersearch_url:
        params = extract_supersearch_params(supersearch_url)
    else:
        params = {}

    params.update(parsed_args)

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if verbose:
        if api_token:
            click.echo(
                "Using api token: %s%s" % (api_token[:4], "x" * (len(api_token) - 4))
            )
        else:
            click.echo(
                "No api token provided. Skipping personally identifiable information."
            )

    if not start_date:
        range_timedelta = parse_relative_date(relative_range)
        start_date = (
            datetime.datetime.strptime(end_date, "%Y-%m-%d") - range_timedelta
        ).strftime("%Y-%m-%d")

    # If it's not daily, then we can do a single facet and print the data out
    # and we're done.
    if not daily:
        params.update({"date": [">=%s" % start_date, "<%s" % end_date]})

        if verbose:
            click.echo("Params: %s" % params)

        facets = fetch_supersearch_facets(
            host, params, api_token=api_token, verbose=verbose
        )

        if format_type == "json":
            click.echo(json.dumps(facets))

        else:
            for facet_name in params.get("_facets", facets.keys()):
                if facet_name not in facets:
                    continue

                headers = [facet_name, "count"]
                facet_data = facets[facet_name]
                rows = [
                    (item["term"], item["count"])
                    for item in sorted(
                        facet_data, key=lambda x: x["count"], reverse=True
                    )
                ]

                if format_type == "tab":
                    click.echo(tableize_tab(headers=headers, rows=rows))
                else:
                    click.echo(tableize_markdown(headers=headers, rows=rows))
        return

    # If it is in daily mode, then we have to do one facet for each day and
    # compose the results.

    # Figure out what facets we're doing
    facet_names = params.get("_facets", ["signature"])

    # Map of facet_name -> (map of date -> (map of value -> count))
    facet_tables = {facet_name: {} for facet_name in facet_names}

    for day_start_date, day_end_date in generate_dates(start_date, end_date):
        params.update({"date": [">=%s" % day_start_date, "<%s" % day_end_date]})

        if verbose:
            click.echo("Params: %s" % params)

        facets = fetch_supersearch_facets(
            host, params, api_token=api_token, verbose=verbose
        )

        for facet_name in facet_names:
            for item in facets.get(facet_name, []):
                facet_tables[facet_name].setdefault(day_start_date, {})[
                    item["term"]
                ] = item["count"]

    # Normalize the data--make sure table rows have all the values
    for facet_name in facet_names:
        values = set()

        table = facet_tables[facet_name]
        for date, value_counts in table.items():
            values = values | set(value_counts.keys())

        for date, value_counts in table.items():
            missing_values = values - set(value_counts.keys())
            for missing_value in missing_values:
                value_counts[missing_value] = 0

    # Print out the normalized data
    if format_type == "json":
        click.echo(json.dumps(facet_tables))

    else:
        for facet_name in facet_names:
            table = facet_tables[facet_name]

            if not table:
                click.echo("%s: no data" % facet_name)
                continue

            some_date = list(table.keys())[0]
            headers = ["date"] + sorted(table[some_date].keys())
            rows = []
            for date, value_counts in table.items():
                rows.append([date] + [item[1] for item in sorted(value_counts.items())])

            if format_type == "tab":
                click.echo(tableize_tab(headers=headers, rows=rows))
            elif format_type == "markdown":
                click.echo(tableize_markdown(headers=headers, rows=rows))

            click.echo("")


if __name__ == "__main__":
    supersearchfacet()
