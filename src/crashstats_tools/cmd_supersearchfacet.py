# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import logging
import os
from urllib.parse import urlparse, parse_qs

import click
from rich.console import Console
from rich.table import Table
from rich import box

from crashstats_tools.utils import (
    AlwaysFirst,
    AlwaysLast,
    DEFAULT_HOST,
    http_get,
    parse_args,
    parse_relative_date,
    sanitize_text,
    tableize_csv,
    tableize_markdown,
    tableize_tab,
)


def thing_to_key(item):
    if isinstance(item, (list, tuple)):
        item = item[0]
    if item == "--":
        return AlwaysFirst()
    if item == "total":
        return AlwaysLast()
    return item


def now():
    return datetime.datetime.now()


def fetch_supersearch_facets(console, host, params, api_token=None, verbose=False):
    """Generator that returns Super Search results

    :arg str host: the host to query
    :arg dict params: dict of super search parameters to base the query on
    :arg str api_token: the API token to use or None
    :arg bool verbose: whether or not to print verbose things

    :returns: response payload as a Python dict

    """
    url = host + "/api/SuperSearch/"

    params["_results_number"] = 0

    if verbose:
        console.print(f"{url} {params}")

    resp = http_get(url=url, params=params, api_token=api_token)
    resp.raise_for_status()
    return resp.json()


def extract_supersearch_params(url):
    """Parses out params from the query string and drops any search-related ones."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Remove search things
    aggs_keys = ("_columns", "_results_number", "_results_offset")
    for key in list(params.keys()):
        if key.startswith(aggs_keys):
            del params[key]

    return params


def convert_cardinality_data(facet_data, facet_name, total):
    """Convert cardinality result to record data

    Data is like::

        {
            "cardinality_product": {
                "value": 6,
            }
        }

    And we want to return::

        {
            "cardinality_product": [
                {"cardinality_product": "value", "value": 6},
            ]
        }

    :arg facet_data: the facet results from the response payload
    :arg facet_name: the facet name

    :returns: a map of facet_name -> list of record dicts

    """
    # FIXME(willkg): this output is redundant--need a better way to structure
    # this
    data = facet_data[facet_name]
    return {facet_name: [{facet_name: "value", "value": data["value"]}]}


def convert_histogram_data(facet_data, facet_name, total):
    """Converts histogram facet data into records

    :arg facet_data: the facet results from the response payload
    :arg facet_name: the facet name

    :returns: a map of facet_name -> list of record dicts

    """
    data = facet_data[facet_name]
    # Map of field_name -> (map of date -> (map of term -> count))
    facet_tables = {}
    for row in data:
        row_term = row["term"]
        if row_term.endswith("T00:00:00+00:00"):
            # Convert timestamps that are just a date at midnight to just the
            # date portion
            row_term = row_term[:10]
        total = row["count"]
        records = {}
        for field_name, field_data in row["facets"].items():
            records = {item["term"]: item["count"] for item in field_data}
            records["--"] = total - sum(records.values())
            records["total"] = total
            facet_tables.setdefault(field_name, {})[row_term] = records

    # Normalize the data--make sure table rows have all the values
    for field_data in facet_tables.values():
        terms = set()
        for date_data in field_data.values():
            terms = terms | set(date_data.keys())

        for date_data in field_data.values():
            missing_terms = terms - set(date_data.keys())
            for missing_term in missing_terms:
                date_data[missing_term] = 0

    # Now convert it to map of field_name -> records
    result = {}
    for field_name, field_data in facet_tables.items():
        keys = list(field_data.values())[0].keys()
        headers = [facet_name] + sorted(keys, key=thing_to_key)

        records = []
        for row_key, row_data in sorted(field_data.items()):
            row = {facet_name: row_key}
            row.update(
                {column: sanitize_text(row_data[column]) for column in headers[1:]}
            )
            records.append(row)
        result[field_name] = records

    return result


def convert_facet_data(facet_data, facet_name, total):
    """Convert facet data to records that can be printed

    This doesn't yet support nested aggregations.

    :arg facet_data: the facet results from the response payload
    :arg facet_name: the facet name

    :returns: a map of facet_name -> {headers: headers, records: records}

    """
    # FIXME(willkg): add support for nested aggregations
    data = facet_data[facet_name]
    records = []
    count_sum = 0
    for item in sorted(data, key=lambda x: x["count"], reverse=True):
        records.append(
            {facet_name: sanitize_text(item["term"]), "count": item["count"]}
        )
        count_sum += item["count"]
    records.append({facet_name: "--", "count": total - count_sum})
    records.append({facet_name: "total", "count": total})

    return {facet_name: records}


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
    default=None,
    show_default=True,
    help="end date for range; YYYY-MM-DD format; defaults to today",
)
@click.option(
    "--relative-range", default="7d", help="relative range ending on end-date"
)
@click.option(
    "--format",
    "format_type",
    default="table",
    show_default=True,
    type=click.Choice(
        ["table", "tab", "csv", "markdown", "json", "raw"], case_sensitive=False
    ),
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
def supersearchfacet(
    ctx,
    host,
    supersearch_url,
    end_date,
    start_date,
    relative_range,
    format_type,
    verbose,
    color,
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

    You can only specify one facet using "--_facets". If you don't specify one,
    it defaults to "signature".

    You can perform histograms, too. For example, this shows you counts for products
    per day for the last week:

    $ supersearchfacet --_histogram.date=product --relative-range=1w

    By default, returned data is a tab-delimited. Tabs and newlines in output
    is escaped. Use "--format" to specify a different output format.

    For list of available fields and Super Search API documentation, see:

    https://crash-stats.mozilla.org/documentation/supersearch/

    https://crash-stats.mozilla.org/documentation/supersearch/api/

    This requires an API token in order to search and get results for protected
    data. Using an API token also reduces rate-limiting. Set the
    CRASHSTATS_API_TOKEN environment variable to your API token value:

    CRASHSTATS_API_TOKEN=xyz supersearchfacet ...

    To create an API token for Crash Stats, visit:

    https://crash-stats.mozilla.org/api/tokens/

    Remember to abide by the data access policy when using data from Crash Stats!
    The policy is specified here:

    https://crash-stats.mozilla.org/documentation/protected_data_access/
    """
    host = host.rstrip("/")

    if not color:
        console = Console(color_system=None, tab_size=None)
    else:
        console = Console(tab_size=None)

    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Require at least one facet specified.
    parsed_args = parse_args(ctx.args)

    if verbose:
        # Set logging to DEBUG because this picks up debug logging from
        # requests which lets us see urls.
        logging.basicConfig(level=logging.DEBUG)

    # Start with params from --url value or product=Firefox
    if supersearch_url:
        params = extract_supersearch_params(supersearch_url)
    else:
        params = {}

    params.update(parsed_args)

    if "_facets" not in params:
        params["_facets"] = []

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

    if "date" not in params and not start_date:
        try:
            range_timedelta = parse_relative_date(relative_range)
        except ValueError as vexc:
            raise click.UsageError(vexc.msg) from vexc

        start_date = (
            datetime.datetime.strptime(end_date, "%Y-%m-%d") - range_timedelta
        ).strftime("%Y-%m-%d")

    if "date" not in params:
        params.update({"date": [">=%s" % start_date, "<%s" % end_date]})

    if verbose:
        console.print(f"Params: {params}")

    facet_data_payload = fetch_supersearch_facets(
        console=console,
        host=host,
        params=params,
        api_token=api_token,
        verbose=verbose,
    )

    if (
        "signature" not in params["_facets"]
        and "signature" in facet_data_payload["facets"]
    ):
        # The Super Search API adds a "signature" facet by default if no other
        # "_facets" are specified even when you don't want it--this removes it
        del facet_data_payload["facets"]["signature"]

    if format_type == "raw":
        console.print_json(json.dumps(facet_data_payload))
        return 0

    total = facet_data_payload["total"]
    facets = facet_data_payload["facets"]

    # We want to print a blank line between things, so we print a blank line
    # before any thing that's not the first thing
    first_thing = True

    for facet_name in facets.keys():
        if facet_name.startswith("cardinality"):
            facet_tables = convert_cardinality_data(facets, facet_name, total)

        elif facet_name.startswith("histogram"):
            facet_tables = convert_histogram_data(facets, facet_name, total)

        else:
            facet_tables = convert_facet_data(facets, facet_name, total)

        if format_type == "json":
            console.print_json(json.dumps(facet_tables))
            continue

        for field, records in facet_tables.items():
            # Grab the first record keys, take out the facet_name, sort, and
            # then add the facet_name first
            headers = list(records[0].keys())
            headers.remove(facet_name)
            headers = [facet_name] + sorted(headers, key=thing_to_key)

            if not first_thing:
                console.print()

            console.print(field)
            if format_type == "table":
                table = Table(show_edge=False, box=box.MARKDOWN)
                for column in headers:
                    table.add_column(column, justify="left")

                for record in records:
                    table.add_row(*[str(record[header]) for header in headers])
                console.print(table)

            elif format_type == "csv":
                for line in tableize_csv(headers=headers, data=records):
                    console.file.write(line + "\n")

            elif format_type == "tab":
                for line in tableize_tab(headers=headers, data=records):
                    console.file.write(line + "\n")

            elif format_type == "markdown":
                for line in tableize_markdown(headers=headers, data=records):
                    console.file.write(line + "\n")

            first_thing = False


if __name__ == "__main__":
    supersearchfacet()
