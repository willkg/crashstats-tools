# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from crashstats_tools.utils import (
    DEFAULT_HOST,
    http_get,
)


# Maximum number of results per page for super search
MAX_PAGE = 1000


class BadRequest(Exception):
    pass


def get_crash_annotations(crash_id, api_token=None, host=DEFAULT_HOST):
    """Fetches crash annotations from host for given crash_id

    The crash annotations from a crash report are saved as a "raw crash" in
    Socorro.

    .. Note::

       If you don't specify an api_token, this only retrieves crash annotations
       that are marked public.

    :arg crash_id: the crash id to retrieve annotation data for
    :arg api_token: the api token to use; defaults to None
    :arg host: the host to retrieve from; defaults to DEFAULT_HOST

    :returns: annotations as a Python dict

    """
    resp = http_get(
        url=f"{host}/api/RawCrash/",
        params={"crash_id": crash_id, "format": "meta"},
        api_token=api_token,
    )

    return resp.json()


def get_dump(crash_id, dump_name, api_token, host=DEFAULT_HOST):
    """Fetches dump, memory_report, or other crash report binary for given crash_id

    .. Note::

       This requires a valid api_token that has the "View Raw Dumps" permission
       from an account with access to protected data.

       https://crash-stats.mozilla.org/api/tokens/

       https://crash-stats.mozilla.org/documentation/protected_data_access/


    :arg crash_id: the crash id to retrieve annotation data for
    :arg dump_name: the name of the dump; something like "memory_report",
        "dump", etc
    :arg api_token: the api token to use
    :arg host: the host to retrieve from; defaults to DEFAULT_HOST

    :returns: annotations as a Python dict

    """
    resp = http_get(
        url=f"{host}/api/RawCrash/",
        params={
            "crash_id": crash_id,
            "format": "raw",
            "name": dump_name,
        },
        api_token=api_token,
    )
    resp.raise_for_status()
    return resp.content


def get_processed_crash(crash_id, api_token=None, host=DEFAULT_HOST):
    """Fetches the processed crash from host for given crash_id

    .. Note::

       If you don't specify an api_token, this only retrieves processed crash
       data marked public.

    :arg crash_id: the crash id to retrieve processed crash data for
    :arg api_token: the api token to use; defaults to None
    :arg host: the host to retrieve from; defaults to DEFAULT_HOST

    :returns: processed crash data as a Python dict

    """
    resp = http_get(
        f"{host}/api/ProcessedCrash/",
        params={"crash_id": crash_id, "format": "meta"},
        api_token=api_token,
    )
    resp.raise_for_status()
    return resp.json()


def supersearch(params, num_results, host=DEFAULT_HOST, api_token=None, logger=None):
    """Performs search and returns generator of result hits

    .. Note::

       This doesn't return facet, aggregation, cardinality, or histogram data.
       If you want that, use supersearch_facet.

    :arg dict params: dict of super search parameters to base the query on
    :arg varies num: number of results to get or INFINITY
    :arg str host: the host to query
    :arg str api_token: the API token to use or None
    :arg varies logger: logger to use for printing what it's doing

    :returns: generator of crash ids

    """
    url = f"{host}/api/SuperSearch/"

    # Set up first page
    params["_results_offset"] = 0
    params["_results_number"] = min(MAX_PAGE, num_results)

    # Fetch pages of crash ids until we've gotten as many as we want or there
    # aren't any more to get
    crashids_count = 0
    while True:
        if logger:
            logger.debug("supersearch: url: %s, params: %r", url, params)

        resp = http_get(url=url, params=params, api_token=api_token)
        resp.raise_for_status()
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


def supersearch_facet(params, api_token=None, host=DEFAULT_HOST, logger=None):
    """Returns super search facet data

    :arg str host: the host to query
    :arg dict params: dict of super search parameters to base the query on
    :arg str api_token: the API token to use or None
    :arg bool verbose: whether or not to print verbose things

    :returns: response payload as a Python dict

    """
    url = f"{host}/api/SuperSearch/"

    # Set _results_number so we don't get search results back, too
    params["_results_number"] = 0

    if logger:
        logger.debug("supersearch_facet: url: %s, params: %r", url, params)

    resp = http_get(
        url=url,
        params=params,
        api_token=api_token,
    )
    resp.raise_for_status()
    return resp.json()
