# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import time

from more_itertools import chunked

from crashstats_tools.utils import (
    DEFAULT_HOST,
    FallbackToPipeAction,
    http_post,
    parse_crashid,
    WrappedTextHelpFormatter,
)


DESCRIPTION = """
Sends specified crashes for reprocessing

This requires CRASHSTATS_API_TOKEN to be set in the environment to a valid API
token.

Note: If you're processing more than 10,000 crashes, you should use a sleep
value that balances the rate of crash ids being added to the queue and the
rate of crash ids being processed. For example, you could use "--sleep 10"
which will sleep for 10 seconds between submitting groups of crashes.

Also, if you're processing a lot of crashes, you should let us know before you
do it.

"""


CHUNK_SIZE = 50
SLEEP_DEFAULT = 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=WrappedTextHelpFormatter, description=DESCRIPTION.strip()
    )
    parser.add_argument(
        "--host", help="host for system to reprocess in", default=DEFAULT_HOST
    )
    parser.add_argument(
        "--sleep",
        help="how long in seconds to sleep before submitting the next group",
        type=int,
        default=SLEEP_DEFAULT,
    )
    parser.add_argument(
        "--allowmany",
        action="store_true",
        help=(
            "don't prompt user about letting us know about reprocessing "
            "more than 10,000 crashes"
        ),
    )
    parser.add_argument(
        "crashid",
        help="one or more crash ids to fetch data for",
        nargs="*",
        action=FallbackToPipeAction,
    )

    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if not api_token:
        print("You need to set CRASHSTATS_API_TOKEN in the environment.")
        return 1

    url = args.host.rstrip("/") + "/api/Reprocessing/"
    print("Sending reprocessing requests to: %s" % url)

    crashids = [
        parse_crashid(crashid.strip())
        for crashid in args.crashid
    ]
    if len(crashids) > 10000 and not args.allowmany:
        print(
            "You are trying to reprocess more than 10,000 crash reports at "
            "once. Please let us know on #breakpad on irc.mozilla.org "
            "before you do this."
        )
        print("")
        print("Pass in --allowmany argument.")
        print("")
        print("Exiting.")
        return 1

    print(
        "Reprocessing %s crashes sleeping %s seconds between groups..."
        % (len(crashids), args.sleep)
    )

    groups = list(chunked(crashids, CHUNK_SIZE))
    for i, group in enumerate(groups):
        print(
            "Processing group ending with %s ... (%s/%s)"
            % (group[-1], i + 1, len(groups))
        )
        resp = http_post(url, data={"crash_ids": group}, api_token=api_token)
        if resp.status_code != 200:
            print(
                "Got back non-200 status code: %s %s" % (resp.status_code, resp.content)
            )
            continue

        # NOTE(willkg): We sleep here because the webapp has a bunch of rate
        # limiting and we don't want to trigger that. It'd be nice if we didn't
        # have to do this.
        time.sleep(args.sleep)

    print("Done!")
    return 0
