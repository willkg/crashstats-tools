# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import logging
import os
from urllib.parse import urlparse, parse_qs


from crashstats_tools.utils import (
    DEFAULT_HOST,
    http_get,
    INFINITY,
    parse_args,
    WrappedTextHelpFormatter,
)


DESCRIPTION = """
Fetches data from Crash Stats using Super Search

There are two ways to run this:

First, you can specify Super Search API fields to generate the query.

For example:

$ supersearch --product=Firefox --num=100 --date=">=2019-07-31"

Second, you can pass in a url from a Super Search on Crash Stats. This command
will then pull out the parameters. You can override those parameters with
command line arguments.

$ supersearch --supersearch-url="longurlhere" --num=100

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
rate-limiting.  Set the CRASHSTATS_API_TOKEN environment variable to your API
token value:

    CRASHSTATS_API_TOKEN=xyz fetch-data crashdata ...

To create an API token for Crash Stats, visit:

    https://crash-stats.mozilla.org/api/tokens/

Remember to abide by the data access policy when using data from Crash Stats!
The policy is specified here:

https://crash-stats.mozilla.org/documentation/memory_dump_access/
"""

MAX_PAGE = 1000


TO_CLEAN = [("\t", "\\t"), ("\r", "\\r"), ("\n", "\\n")]


def clean_whitespace(text):
    text = text or ""

    for s, replace in TO_CLEAN:
        text = text.replace(s, replace)
    return text


def fetch_supersearch(host, params, num_results, api_token=None, verbose=False):
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
            print(url, params)

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

    for key in list(params.keys()):
        # Remove any aggs
        if key.startswith(["_facets", "_aggs", "_histogram", "_cardinality"]):
            del params[key]

    return params


def main(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=WrappedTextHelpFormatter, description=DESCRIPTION.strip()
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help="host for system to fetch crashids from"
    )
    parser.add_argument(
        "--supersearch-url", default="", help="Super Search url to base query on"
    )
    parser.add_argument(
        "--num",
        default=100,
        help='number of crash ids you want or "all" for all of them',
    )
    parser.add_argument(
        "--format", default="tab", choices=["tab", "json"], help="format for output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase verbosity of output"
    )

    if argv is None:
        args, supersearch_args = parser.parse_known_args()
    else:
        args, supersearch_args = parser.parse_known_args(argv)

    if args.verbose:
        # Set logging to DEBUG because this picks up debug logging from
        # requests which lets us see urls.
        logging.basicConfig(level=logging.DEBUG)

    host = args.host.rstrip("/")

    # Start with params from --url value or product=Firefox
    if args.supersearch_url:
        params = extract_supersearch_params(args.supersearch_url)
    else:
        params = {}

    params.update(parse_args(supersearch_args))

    if "_columns" not in params:
        params["_columns"] = ["uuid"]

    if "_sort" not in params and "date" not in params:
        # If _sort and date aren't in params, then we're going to assume the
        # user wants the most recent crash reports.
        params["_sort"] = ["-date"]

    num_results = args.num
    if num_results == "all":
        num_results = INFINITY

    else:
        try:
            num_results = int(num_results)
        except ValueError:
            print('num needs to be an integer or "all"')
            return 1

    if args.verbose:
        print("Params: %s" % params)

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if args.verbose:
        if api_token:
            print("Using api token: %s%s" % (api_token[:4], "x" * (len(api_token) - 4)))
        else:
            print(
                "No api token provided. Skipping dumps and personally identifiable information."
            )

    for hit in fetch_supersearch(
        host, params, num_results, api_token=api_token, verbose=args.verbose
    ):
        if args.format == "tab":
            print(
                "\t".join(
                    [clean_whitespace(hit[field]) for field in params["_columns"]]
                )
            )
        elif args.format == "json":
            print(json.dumps(hit))

    return 0
