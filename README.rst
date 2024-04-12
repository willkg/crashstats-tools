================
crashstats-tools
================

Command line tools and library for interacting with Crash Stats
(`<https://crash-stats.mozilla.org/>`_).

:Code: https://github.com/willkg/crashstats-tools
:Documentation: Check the ``README.rst`` file
:Changelog: Check the ``HISTORY.rst`` file
:Issue tracker: https://github.com/willkg/crashstats-tools/issues
:License: MPLv2
:Chat: `#crashreporting matrix channel <https://chat.mozilla.org/#/room/#crashreporting:mozilla.org>`__
:Community Participation Guidelines: `<https://github.com/willkg/crashstats-tools/blob/main/CODE_OF_CONDUCT.md>`_


Installing
==========

crashstats-tools is available on `PyPI <https://pypi.org>`_. You can install it
with `pipx <https://pipxproject.github.io/pipx/>`_::

    $ pipx install crashstats-tools


For developing crashstats-tools, clone the Git repository, create a virtual
environment, and install crashstats-tools and dev dependencies with::

    $ pip install -e '.[dev]'


Support
=======

This is a project that I spent some time on because it seemed helpful to me
and others. I use it regularly for Crash Stats investigations and reprocessing.
However, I'm not you! If you have any problems, please write up an issue in the
issue tracker and I'll get to it when I'm able.

If you use this, like it, appreciate it, or have any positive feeling, please
give it a GitHub star. That helps me:

1. have a proxy for knowing whether it's being used
2. prioritize my time working on this project
3. have a hand-wavey list of users in case I have questions and need to ask
   for advice


Tools
=====

.. [[[cog
    from click.testing import CliRunner

    def execute_help(cmd):
        result = CliRunner().invoke(supersearch, ["--help"])
        cog.out("\n::\n\n")
        for line in result.output.splitlines():
            if line.strip():
                cog.out(f"   {line}\n")
            else:
                cog.out("\n")
        cog.out("\n")
   ]]]
.. [[[end]]]

supersearch
-----------

.. [[[cog
    from crashstats_tools.cmd_supersearch import supersearch
    execute_help(supersearch)
   ]]]

::

   Usage: supersearch [OPTIONS]

     Performs a basic search on Crash Stats using the Super Search API and outputs
     the results.

     A basic search uses filters and can span multiple pages of results. A basic
     search cannot include facets, aggregations, histograms, or cardinalities. For
     those, use supersearchfacet.

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearch --product=Firefox --num=10

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the filter parameters. You can override those parameters
     with command line arguments.

     $ supersearch --supersearch-url='https://crash-stats.mozilla.org/search/...'

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables or parse escape sequences.

     You can specify returned fields using the Super Search field "_columns".

     For example:

     $ supersearch --_columns=uuid --_columns=product --_columns=build_id

     Results are tab-delimited by default. You can specify other output formats
     using "--format". Tabs and newlines in output are escaped.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This requires an API token in order to search and get results for protected
     data fields. Using an API token also reduces rate-limiting. Set the
     CRASHSTATS_API_TOKEN environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz supersearch ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                     host for system to fetch crashids from
                                     [default: https://crash-stats.mozilla.org]
     --supersearch-url TEXT          Super Search url to base query on
     --num TEXT                      number of crash ids you want or "all" for all
                                     of them  [default: 100]
     --headers / --no-headers        whether or not to show table headers
                                     [default: no-headers]
     --format [table|tab|csv|json|markdown]
                                     format to print output  [default: tab]
     --verbose / --no-verbose        whether to print debugging output  [default:
                                     no-verbose]
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically  [default:
                                     color]
     --help                          Show this message and exit.

.. [[[end]]]

Fetch 10 crash ids for Firefox::

    $ supersearch --num=10 --product=Firefox

Fetch all crash reports that have ``libc2.30.so/E22A1E7AEF7C58504AF2C60A5AD3A7AE0``
in the ``modules_in_stack`` field::

    $ supersearch --modules_in_stack=libc2.30.so/E22A1E7AEF6C58504AF2C60A5AD3A7AE0

This is helpful when you need to reprocess crash reports after uploading symbols
for a module that we didn't have symbols for.

Fetch all crash reports that have ``libgallium_dri.so`` in the
``modules_in_stack`` field::

   $ supersearch --modules_in_stack='^libgallium_dri.so'

Fetch 57 crash ids that match a Super Search query::

    $ supersearch --num=57 \
        --supersearch-url='https://crash-stats.mozilla.org/search/?release_channel=nightly&version=70.0a1&product=Firefox&_sort=-date'

Use single quotes for values so that your shell doesn't do any shell expansion.

Fetch uuid, product, version, and build_id for crash reports that have "OOM" in
the signature::

    $ supersearch --_columns=uuid --_columns=product --_columns=version \
        --_columns=build_id --signature='~OOM'

Note that this doesn't support Super Search aggregations--use
the ``supersearchfacet`` command for that.

See Super Search API documentation for details on notation and fields:

* https://crash-stats.mozilla.org/documentation/supersearch/
* https://crash-stats.mozilla.org/documentation/supersearch/api/


supersearchfacet
----------------

.. [[[cog
   from crashstats_tools.cmd_supersearchfacet import supersearchfacet
   execute_help(supersearchfacet)
   ]]]

::

   Usage: supersearch [OPTIONS]

     Performs a basic search on Crash Stats using the Super Search API and outputs
     the results.

     A basic search uses filters and can span multiple pages of results. A basic
     search cannot include facets, aggregations, histograms, or cardinalities. For
     those, use supersearchfacet.

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearch --product=Firefox --num=10

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the filter parameters. You can override those parameters
     with command line arguments.

     $ supersearch --supersearch-url='https://crash-stats.mozilla.org/search/...'

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables or parse escape sequences.

     You can specify returned fields using the Super Search field "_columns".

     For example:

     $ supersearch --_columns=uuid --_columns=product --_columns=build_id

     Results are tab-delimited by default. You can specify other output formats
     using "--format". Tabs and newlines in output are escaped.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This requires an API token in order to search and get results for protected
     data fields. Using an API token also reduces rate-limiting. Set the
     CRASHSTATS_API_TOKEN environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz supersearch ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                     host for system to fetch crashids from
                                     [default: https://crash-stats.mozilla.org]
     --supersearch-url TEXT          Super Search url to base query on
     --num TEXT                      number of crash ids you want or "all" for all
                                     of them  [default: 100]
     --headers / --no-headers        whether or not to show table headers
                                     [default: no-headers]
     --format [table|tab|csv|json|markdown]
                                     format to print output  [default: tab]
     --verbose / --no-verbose        whether to print debugging output  [default:
                                     no-verbose]
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically  [default:
                                     color]
     --help                          Show this message and exit.

.. [[[end]]]

See the breakdown of crash reports by product for the last 7 days::

    $ supersearchfacet --_facets=product

See crashes broken down by product and down by day for the last 7 days::

    $ supersearchfacet --_histogram.date=product --relative=range=7d

Histograms, facets, aggs, and cardinality can be filtered using Super Search
filters. See crashes in Firefox by release channel broken down by day for the
last 7 days::

    $ supersearchfacet \
        --_histogram.date=release_channel \
        --release_channel=nightly \
        --release_channel=beta \
        --release_channel=release \
        --release_channel=esr \
        --product=Firefox \
        --relative-range=7d

Get the table in Markdown for easy cut-and-paste into Markdown things::

    $ supersearchfacet --_histogram.date=product --relative=range=7d \
        --format=markdown

See Super Search API documentation for details on notation and fields:

* https://crash-stats.mozilla.org/documentation/supersearch/
* https://crash-stats.mozilla.org/documentation/supersearch/api/


fetch-data
----------

.. [[[cog
   from crashstats_tools.cmd_fetch_data import fetch_data
   execute_help(fetch_data)
   ]]]

::

   Usage: supersearch [OPTIONS]

     Performs a basic search on Crash Stats using the Super Search API and outputs
     the results.

     A basic search uses filters and can span multiple pages of results. A basic
     search cannot include facets, aggregations, histograms, or cardinalities. For
     those, use supersearchfacet.

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearch --product=Firefox --num=10

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the filter parameters. You can override those parameters
     with command line arguments.

     $ supersearch --supersearch-url='https://crash-stats.mozilla.org/search/...'

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables or parse escape sequences.

     You can specify returned fields using the Super Search field "_columns".

     For example:

     $ supersearch --_columns=uuid --_columns=product --_columns=build_id

     Results are tab-delimited by default. You can specify other output formats
     using "--format". Tabs and newlines in output are escaped.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This requires an API token in order to search and get results for protected
     data fields. Using an API token also reduces rate-limiting. Set the
     CRASHSTATS_API_TOKEN environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz supersearch ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                     host for system to fetch crashids from
                                     [default: https://crash-stats.mozilla.org]
     --supersearch-url TEXT          Super Search url to base query on
     --num TEXT                      number of crash ids you want or "all" for all
                                     of them  [default: 100]
     --headers / --no-headers        whether or not to show table headers
                                     [default: no-headers]
     --format [table|tab|csv|json|markdown]
                                     format to print output  [default: tab]
     --verbose / --no-verbose        whether to print debugging output  [default:
                                     no-verbose]
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically  [default:
                                     color]
     --help                          Show this message and exit.

.. [[[end]]]

This lets you download raw crash, dumps, and processed crash from Crash Stats.

Fetch processed crash data for specific crash id::

    $ fetch-data --no-raw --no-dumps --processed 723cacd6-1684-420e-a1c7-f04240190731

Fetch raw crash data using supersearch command to generate crash ids::

    $ supersearch --product=Firefox --num=10 | \
        fetch-data --raw --no-dumps --no-processed crashdir


reprocess
---------

.. [[[cog
   from crashstats_tools.cmd_reprocess import reprocess
   execute_help(reprocess)
   ]]]

::

   Usage: supersearch [OPTIONS]

     Performs a basic search on Crash Stats using the Super Search API and outputs
     the results.

     A basic search uses filters and can span multiple pages of results. A basic
     search cannot include facets, aggregations, histograms, or cardinalities. For
     those, use supersearchfacet.

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearch --product=Firefox --num=10

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the filter parameters. You can override those parameters
     with command line arguments.

     $ supersearch --supersearch-url='https://crash-stats.mozilla.org/search/...'

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables or parse escape sequences.

     You can specify returned fields using the Super Search field "_columns".

     For example:

     $ supersearch --_columns=uuid --_columns=product --_columns=build_id

     Results are tab-delimited by default. You can specify other output formats
     using "--format". Tabs and newlines in output are escaped.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This requires an API token in order to search and get results for protected
     data fields. Using an API token also reduces rate-limiting. Set the
     CRASHSTATS_API_TOKEN environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz supersearch ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                     host for system to fetch crashids from
                                     [default: https://crash-stats.mozilla.org]
     --supersearch-url TEXT          Super Search url to base query on
     --num TEXT                      number of crash ids you want or "all" for all
                                     of them  [default: 100]
     --headers / --no-headers        whether or not to show table headers
                                     [default: no-headers]
     --format [table|tab|csv|json|markdown]
                                     format to print output  [default: tab]
     --verbose / --no-verbose        whether to print debugging output  [default:
                                     no-verbose]
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically  [default:
                                     color]
     --help                          Show this message and exit.

.. [[[end]]]

Reprocess an individual crash report::

    $ reprocess 723cacd6-1684-420e-a1c7-f04240190731

Reprocess crash reports based on a supersearch::

    $ supersearch --num=5 | reprocess

.. Note::

   The ``reprocess`` command requires that you set ``CRASHSTATS_API_TOKEN`` in
   your environment with an API token that has the "Reprocess Crashes"
   permission.


.. Note::

   If you intend to reprocess more than 10,000 crash reports, please tell
   us first.


API token
=========

For ``supersearch`` and ``fetch-data``, you need to use a API token to:

* download data containing personally identifiable information
* download security sensitive data
* get out from the shadow of extreme API use rate limiting

You need an API token for ``reprocess``--it doesn't work without one.

If you have access, you can generate an API token here:

https://crash-stats.mozilla.org/api/tokens/

Once you have acquired one, set the ``CRASHSTATS_API_TOKEN`` environment
variable when using crashstats-tools commands.

Remember to abide by the data access policy when using data from Crash Stats!
The policy is specified here:

https://crash-stats.mozilla.org/documentation/memory_dump_access/


Use cases
=========

These tools are helpful when downloading data for analysis as well as
downloading data to test other tools with.


Example 1
---------

I want to collect a bunch of crash report data to look at possible values of an
annotation in Firefox crash reports that's not available in Super Search, yet.

Since I'm looking just at annotations, all I need is the raw crash.

I would do something like this::

    $ mkdir crashdata
    $ supersearch --product=Firefox --num=1000 | \
        fetch-data --raw --no-dumps --no-processed crashdata

Then I can use ``jq`` or whatever to look at the crash report data in
``crashdata/raw_crash/``.


Example 2
---------

I want to test out a new JIT analysis tool that works on minidump files.

I would write a script like this::

    #!/bin/bash
    
    CRASHSTATS_API_TOKEN=foo
    DATADIR=./crashdata
    CRASHIDS=$(supersearch --product=Firefox --num=1000)
    
    mkdir -p "${DATADIR}"
    
    for crashid in ${CRASHIDS}
    do
        echo "crashid ${crashid}"
        fetch-data --raw --dumps --no-processed "${DATADIR}" "${crashid}"
    
        # Not all crash reports have dumps--we only want to run analysis
        # on the ones that do.
        if [[ -e "crashdata/dump/${crashid}" ]]
        then
            echo "analyze dump ${crashid}..."
            # run my tool on the dump
        fi
    done
    

Example 3
---------

I want to get a list of crash ids for today (2019-07-30) where
``DOMFissionEnabled`` exists in the crash report.

I would do this::

    $ supersearch --date=">=2019-07-30" --date='<2019-07-31' \
        --dom_fission_enabled='!__null__'


Example 4
---------

I want to see number of crash reports for the last 14 days broken down by day
and by product where ``DOMFissionEnabled`` exists in the crash report.

I would do this::

    $ supersearchfacet --period=daily --format=markdown --relative-range=14d \
        --dom_fission_enabled='!__null__' --_facets=product


Library
=======

Further, this provides a library interface to some Crash Stats API endpoints:

``crashstats_tools.libcrashstats``

``get_crash_annotations(crash_id, api_token=None, host=DEFAULT_HOST)``
    Fetches crash annotations for a given crash report.

    If you don't provide an API token, then it only returns crash annotations
    that are marked public.

``get_dump(crash_id, dump_name, api_token, host=DEFAULT_HOST)``
    Fetches dumps, memory reports, and other crash report binaries for given
    crash id.

    This requires an api token.

``get_processed_crash(crash_id, api_token=None, host=DEFAULT_HOST)``
    Fetches the processed crash for given crash id.

``supersearch(params, num_results, host=DEFAULT_HOST, api_token=None, logger=None)``
    Performs a super search and returns generator of result hits.

    This doesn't return facet, aggregation, cardinality, or histogram data.
    If you want that, use ``supersearch_facet``.

``supersearch_facet(params, api_token=None, host=DEFAULT_HOST, logger=None)``
    Performs a super search and returns facet data


Prior art and related projects
==============================

https://github.com/mozilla/libmozdata
    Python library which has a ``Supersearch`` class for performing queries and
    a ``ProcessedCrash`` class for fetching processed crash data.

https://github.com/mozilla-services/socorro
    Socorro (the code base for Crash Stats) has a Docker-based local dev
    environment which includes a series of commands for manipulating data.

    https://socorro.readthedocs.io/en/latest/service/processor.html#processing-crashes
