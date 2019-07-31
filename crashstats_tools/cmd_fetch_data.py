# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import os

from crashstats_tools.utils import (
    DEFAULT_HOST,
    FallbackToPipeAction,
    FlagAction,
    http_get,
    JsonDTEncoder,
    WrappedTextHelpFormatter,
)


DESCRIPTION = """
Fetches crash data from Crash Stats (https://crash-stats.mozilla.org/) system.
"""


EPILOG = """
Given one or more crash ids via command line or stdin (one per line), fetches
crash data and puts it in specified directory.

Crash data is split up into directories: raw_crash/, dump_names/,
processed_crash/, and directories with the same name as the dump type.

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


def create_dir_if_needed(d):
    if not os.path.exists(d):
        os.makedirs(d)


def fetch_crash(
    host, fetchraw, fetchdumps, fetchprocessed, outputdir, api_token, crash_id
):
    """Fetch crash data and save to correct place on the file system

    http://antenna.readthedocs.io/en/latest/architecture.html#aws-s3-file-hierarchy

    """
    if fetchraw:
        # Fetch raw crash metadata
        print("Fetching raw %s" % crash_id)
        resp = http_get(
            url=host + "/api/RawCrash/",
            params={"crash_id": crash_id, "format": "meta"},
            api_token=api_token,
        )

        # Save raw crash to file system
        raw_crash = resp.json()
        fn = os.path.join(outputdir, "raw_crash", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(raw_crash, fp, cls=JsonDTEncoder, indent=2, sort_keys=True)

    if fetchdumps:
        # Save dump_names to file system
        dump_names = raw_crash.get("dump_checksums", {}).keys()
        fn = os.path.join(outputdir, "dump_names", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(dump_names, fp)

        # Fetch dumps
        for dump_name in dump_names:
            print("Fetching dump %s/%s" % (crash_id, dump_name))

            # We store "upload_file_minidump" as "dump", so we need to use that
            # name when requesting from the RawCrash api
            file_name = dump_name
            if file_name == "upload_file_minidump":
                file_name = "dump"

            resp = http_get(
                url=host + "/api/RawCrash/",
                params={"crash_id": crash_id, "format": "raw", "name": file_name},
                api_token=api_token,
            )

            if resp.status_code != 200:
                raise Exception(
                    "Something unexpected happened. status_code %s, content %s"
                    % (resp.status_code, resp.content)
                )

            fn = os.path.join(outputdir, dump_name, crash_id)
            create_dir_if_needed(os.path.dirname(fn))
            with open(fn, "wb") as fp:
                fp.write(resp.content)

    if fetchprocessed:
        # Fetch processed crash data
        print("Fetching processed %s" % crash_id)
        resp = http_get(
            host + "/api/ProcessedCrash/",
            params={"crash_id": crash_id, "format": "meta"},
            api_token=api_token,
        )

        # Save processed crash to file system
        fn = os.path.join(outputdir, "processed_crash", crash_id)
        create_dir_if_needed(os.path.dirname(fn))
        with open(fn, "w") as fp:
            json.dump(resp.json(), fp, cls=JsonDTEncoder, indent=2, sort_keys=True)


def main(argv=None):
    """Fetches crash data from Crash Stats."""
    parser = argparse.ArgumentParser(
        formatter_class=WrappedTextHelpFormatter,
        description=DESCRIPTION.strip(),
        epilog=EPILOG.strip(),
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="host to pull crash data from; this needs to match CRASHSTATS_API_TOKEN value",
    )
    parser.add_argument(
        "--raw",
        "--no-raw",
        dest="fetchraw",
        action=FlagAction,
        default=True,
        help="whether or not to save raw crash data",
    )
    parser.add_argument(
        "--dumps",
        "--no-dumps",
        dest="fetchdumps",
        action=FlagAction,
        default=True,
        help="whether or not to save dumps",
    )
    parser.add_argument(
        "--processed",
        "--no-processed",
        dest="fetchprocessed",
        action=FlagAction,
        default=False,
        help="whether or not to save processed crash data",
    )

    parser.add_argument("outputdir", help="directory to place crash data in")
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

    if args.fetchdumps and not args.fetchraw:
        print("You cannot fetch dumps without also fetching the raw crash. Exiting.")
        return 1

    # Validate outputdir and exit if it doesn't exist or isn't a directory
    outputdir = args.outputdir
    if os.path.exists(outputdir) and not os.path.isdir(outputdir):
        print("%s is not a directory. Please fix. Exiting." % outputdir)
        return 1

    # Sort out API token existence
    api_token = os.environ.get("CRASHSTATS_API_TOKEN")
    if api_token:
        print("Using api token: %s%s" % (api_token[:4], "x" * (len(api_token) - 4)))
    else:
        print(
            "No api token provided. Skipping dumps and personally identifiable information."
        )

    for crash_id in args.crashid:
        crash_id = crash_id.strip()

        print("Working on %s..." % crash_id)
        fetch_crash(
            host=args.host,
            fetchraw=args.fetchraw,
            fetchdumps=args.fetchdumps if api_token else False,
            fetchprocessed=args.fetchprocessed,
            outputdir=outputdir,
            api_token=api_token,
            crash_id=crash_id,
        )

    return 0
