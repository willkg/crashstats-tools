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

from crashstats_tools.libcrashstats import supersearch_facet
from crashstats_tools.utils import (
    ConsoleLogger,
    DEFAULT_HOST,
    parse_args,
    parse_relative_date,
    sanitize_text,
    tableize_csv,
    tableize_markdown,
    tableize_tab,
    thing_to_key,
)


def extract_supersearch_params(url):
    """Parses out params from the query string and drops any search-related ones.

    :arg url: a url string

    :returns: dict of params from url minus params specific to supersearch
        results

    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Remove search things
    aggs_keys = ("_columns", "_results_number", "_results_offset")
    for key in list(params.keys()):
        if key.startswith(aggs_keys):
            del params[key]

    return params


def convert_histogram_data(facet_name, facet_data):
    """Converts histogram facet data into records

    :arg facet_name: the facet name
    :arg facet_data: the facet results from the response payload

    :returns: a map of facet_name -> list of record dicts

    """
    # Map of field_name -> (map of date -> (map of term -> count))
    facet_tables = {}
    for row in facet_data:
        row_term = row["term"]
        if row_term.endswith("T00:00:00+00:00"):
            # Convert timestamps that are just a date at midnight to just the
            # date portion
            row_term = row_term[:10]
        total = row["count"]
        records = {}
        for field_name, field_data in row["facets"].items():
            if field_name.startswith("cardinality"):
                records = {"value": field_data["value"]}
            else:
                records = {item["term"]: item["count"] for item in field_data}
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


def flatten_facets(facet_data):
    """Flattens facet value data.

    :arg facet_data: map of key -> term_counts

    :returns: map of key -> list of record dicts

    """
    if not facet_data:
        return {}

    flattened_facet_data = {}
    for key, term_counts in facet_data.items():
        if key.startswith("cardinality"):
            # term_counts here is something like: {"value": 6}
            #
            # convert to [{key: "value", "value": 6}]
            flattened_facet_data[key] = [{key: "value", "value": term_counts["value"]}]

        elif key.startswith("histogram"):
            flattened_facet_data[key] = convert_histogram_data(key, term_counts)

        else:
            for term_count_item in term_counts:
                term = term_count_item["term"]
                count = term_count_item["count"]

                if "facets" in term_count_item:
                    term_counts_dict = flatten_facets(term_count_item["facets"])
                    for term_key, term_data in term_counts_dict.items():
                        new_key = f"{key} / {term_key}"
                        for item in term_data:
                            new_data = {
                                new_key: f"{term} / {item[term_key]}",
                            }
                            # cardinality has "value", while facets have
                            # "count" so we need to handle both here
                            new_data["count"] = item.get("count", item.get("value"))
                            flattened_facet_data.setdefault(new_key, []).append(
                                new_data
                            )

                else:
                    new_data = {key: term, "count": count}
                    flattened_facet_data.setdefault(key, []).append(new_data)

    return flattened_facet_data


def generate_facet_tables(leftover_count, facet_name, facet_data, total):
    """
    :returns: a map of facet_name -> {headers: headers, records: records}

    """
    records = []
    count_sum = 0
    for term, count in sorted(facet_data.items(), key=lambda x: x[1], reverse=True):
        records.append({facet_name: sanitize_text(term), "count": count})
        count_sum += count

    if not facet_name.startswith("cardinality"):
        if leftover_count:
            records.append({facet_name: "--", "count": total - count_sum})
        records.append({facet_name: "total", "count": total})

    return {facet_name: records}


DATE_TEMPLATES = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S+%z",
]


def is_weekend(value):
    """Denotes whether this date is a weekend.

    :arg value: a string value representing a date/datetime

    :returns: whether or not this is a weekend

    """
    for template in DATE_TEMPLATES:
        try:
            dt = datetime.datetime.strptime(value, template)
            return dt.weekday() in [5, 6]
        except ValueError:
            continue
    return False


def fix_value(value, denote_weekends=False):
    """Sanitizes text and adds ``**`` if it's a weekend if specified

    :arg value: the text to operate on
    :arg denote_weekends: whether or not to denote weekend if the item is a
        date/datetime and it's a weekend

    :returns: the final value

    """
    value = sanitize_text(str(value))
    if denote_weekends and isinstance(value, str) and is_weekend(value):
        return f"{value} **"

    return value


@click.command(
    context_settings={
        "show_default": True,
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
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
    default="today",
    show_default=True,
    help="end date for range; YYYY-MM-DD format",
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
        + "when stdout is not an interactive terminal automatically"
    ),
)
@click.option(
    "--denote-weekends/--no-denote-weekends",
    default=False,
    help=(
        "This will add a * for values that are datestamps and on a Saturday or Sunday."
    ),
)
@click.option(
    "--leftover-count/--no-leftover-count",
    default=False,
    help=(
        "Calculates the leftover that is the difference between the total "
        + "minus the sum of all term counts"
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
    denote_weekends,
    leftover_count,
):
    """Fetches facet data from Crash Stats using Super Search

    There are two ways to run this:

    First, you can specify Super Search API fields to generate the query.

    For example:

    $ supersearchfacet --product=Firefox --_facets=version

    Second, you can pass in a url from a Super Search on Crash Stats. This
    command will then pull out the parameters. You can override those
    parameters with command line arguments.

    \b
    $ supersearchfacet --_facets=version \\
        --supersearch-url='https://crash-stats.mozilla.org/search/...'

    Make sure to use single quotes when specifying values so that your shell
    doesn't expand variables.

    You can get a facet of a field using ``_facets``.

    For example, this filters on Firefox and returns a facet on version
    for the last 7 days (the default time range).

    $ supersearchfacet --product=Firefox --_facets=version

    You can get cardinality (number of possible values), too. For example, this
    shows the number of different versions for Firefox crash reports in the
    last 7 days.

    $ supersearchfacet --product=Firefox --_facets=_cardinality.version

    You can perform histograms. For example, this shows you counts for products
    per day for the last week:

    $ supersearchfacet --_histogram.date=product --relative-range=1w

    You can get a cardinality for the data for a field. For example,
    this tells you how many build ids there were for Firefox 124:

    $ supersearchfacet --product=Firefox --version=124.0 \
        --_facets=_cardinality.build_id

    You can do nested aggregations. For example, this shows the count
    of crash reports by product by release channel:

    $ supersearchfacet --_aggs.product=release_channel

    This shows count of crash reports by product, version, cardinality of
    install_time:

    $ supersearchfacet --_aggs.product.version=_cardinality.install_time

    Make sure to specify at least one of ``_facets``, ``_aggs``,
    ``_histogram``, or ``_cardinality``.

    By default, returned data is in a table. Tabs and newlines in output is
    escaped. Use ``--format`` to specify a different output format.

    For list of available fields and Super Search API documentation, see:

    https://crash-stats.mozilla.org/documentation/supersearch/

    https://crash-stats.mozilla.org/documentation/supersearch/api/

    This requires an API token in order to search and get results for protected
    data fields. Using an API token also reduces rate-limiting. Set the
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
        console_err = Console(color_system=None, tab_size=None, stderr=True)
    else:
        console = Console(tab_size=None)
        console_err = Console(tab_size=None, stderr=True)

    if end_date == "today":
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
            console.print(f"Using API token: {masked_token}")
        else:
            console.print(
                "[yellow]No API token provided. Set CRASHSTATS_API_TOKEN in the "
                + "environment.[/yellow]"
            )
            console.print("[yellow]Skipping dumps and protected data.[/yellow]")

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

    facet_data_payload = supersearch_facet(
        params=params,
        api_token=api_token,
        host=host,
        logger=ConsoleLogger(console) if verbose else None,
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
        return

    total = facet_data_payload["total"]
    facets = facet_data_payload["facets"]

    flattened_facets = flatten_facets(facets)

    # Add leftover and total records
    for facet_name, records in flattened_facets.items():
        if not facet_name.startswith(("histogram", "cardinality")):
            if leftover_count:
                record_sum = sum(rec["count"] for rec in records)
                records.append({facet_name: "--", "count": total - record_sum})

            records.append({facet_name: "total", "count": total})

        elif facet_name.startswith("histogram"):
            if leftover_count:
                for _, rows in records.items():
                    for row in rows:
                        count = 0
                        for key, val in row.items():
                            if key == facet_name:
                                continue
                            elif key == "total":
                                count -= int(val)
                            else:
                                count += int(val)
                        row["--"] = str(count)

    if format_type == "json":
        console.print_json(json.dumps(flattened_facets))
        return

    # We want to print a blank line between things, so we print a blank line
    # before any thing that's not the first thing
    first_thing = True
    for facet_name, records in flattened_facets.items():
        if not first_thing:
            console.print()

        print_table(
            console=console,
            format_type=format_type,
            denote_weekends=denote_weekends,
            facet_name=[facet_name],
            records=records,
        )
        first_thing = False

    if first_thing:
        # This is weird--it means we didn't print any tables, so something is
        # wrong.
        console_err.print("No output--something went wrong.")
        console_err.print(f"Host: {host}")
        if api_token:
            masked_token = api_token[:4] + ("x" * (len(api_token) - 4))
            console_err.print(f"Using API token: {masked_token}")
        else:
            console_err.print("Not using API token.")
        console_err.print(f"Params sent: {params}")
        console_err.print(f"Output returned: {facet_data_payload}")
        ctx.exit(1)


def print_table(console, format_type, denote_weekends, facet_name, records):
    if isinstance(records, dict):
        for sub_facet_name, sub_records in records.items():
            print_table(
                console=console,
                format_type=format_type,
                denote_weekends=denote_weekends,
                facet_name=facet_name + [sub_facet_name],
                records=sub_records,
            )
        return

    # Grab the first record keys, take out the facet_name, sort, and then
    # add the facet_name first
    headers = list(records[0].keys())
    headers.remove(facet_name[0])
    headers = [facet_name[0]] + sorted(headers, key=thing_to_key)

    records = [
        {key: fix_value(val, denote_weekends) for key, val in record.items()}
        for record in records
    ]

    console.print(".".join(facet_name))
    if format_type == "table":
        table = Table(show_edge=False, box=box.MARKDOWN)
        for column in headers:
            table.add_column(column, justify="left")

        for record in records:
            table.add_row(*[record[header] for header in headers])
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


if __name__ == "__main__":
    supersearchfacet()
