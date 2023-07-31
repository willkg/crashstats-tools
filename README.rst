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

crashstats-tools is available on `PyPI <https://pypi.org>`_. You can install
it with::

    $ pip install --user crashstats-tools

Since it has commands that you want to use, you probably want to
install it with `pipx <https://pipxproject.github.io/pipx/>`_::

    $ pipx install crashstats-tools


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

supersearch
-----------

.. [[[cog
    from crashstats_tools.cmd_supersearch import supersearch
    from click.testing import CliRunner
    result = CliRunner().invoke(supersearch, ["--help"])
    cog.out("::\n\n")
    for line in result.output.splitlines():
        if line.strip():
            cog.out(f"   {line}\n")
        else:
            cog.out("\n")
    ]]]
::

   Usage: supersearch [OPTIONS]

     Fetches data from Crash Stats using Super Search

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearch --product=Firefox --num=100 --date='>=2019-07-31'

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the parameters. You can override those parameters with
     command line arguments.

     $ supersearch --supersearch-url='longurlhere' --num=100

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables.

     Returned fields are tab-delimited. You can specify them using the Super Search
     field "_columns".

     For example:

     $ supersearch --_columns=uuid --_columns=product --_columns=build_id
     --_columns=version

     Results are tab-delimited. Tabs and newlines in output is escaped.

     This doesn't support any of the aggregations at this time.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This requires an API token in order to search and get results for protected
     data. Using an API token also reduces rate-limiting. Set the
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
     --format [table|tab|json|markdown]
                                     format to print output  [default: tab]
     --verbose / --no-verbose        whether to print debugging output
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically
     --help                          Show this message and exit.
.. [[[end]]]

Fetch 10 crash ids for Firefox::

    $ supersearch --num=10 --product=Firefox

Fetch all crash reports that have ``libc2.30.so/E22A1E7AEF7C58504AF2C60A5AD3A7AE0``
in the ``modules_in_stack`` field::

    $ supersearch --modules_in_stack=libc2.30.so/E22A1E7AEF6C58504AF2C60A5AD3A7AE0

This is helpful when you need to reprocess crash reports after uploading symbols
for a module that we didn't have symbols for.

Fetch all crash reports that have ``libfenix.so`` in the ``modules_in_stack``
field::

   $ supersearch --verbose --modules_in_stack='^libfenix.so'

Fetch 57 crash ids that match a Super Search query::

    $ supersearch --num=57 --supersearch-url='https://crash-stats.mozilla.org/search/?release_channel=nightly&version=70.0a1&product=Firefox&_sort=-date'

Use single quotes for values so that your shell doesn't do any shell expansion.

Fetch uuid, product, version, and build_id for crash reports that have "OOM" in
the signature::

    $ supersearch --_columns=uuid --_columns=product --_columns=version \
        --_columns=build_id --signature='~OOM'

Results are formatted as tab-delimited by default. JSON output is also
available.

Note that this doesn't support Super Search aggregations--use
``supersearchfacet`` for that.

See Super Search API documentation for details on notation and fields:

* https://crash-stats.mozilla.org/documentation/supersearch/
* https://crash-stats.mozilla.org/documentation/supersearch/api/


supersearchfacet
----------------

.. [[[cog
    from crashstats_tools.cmd_supersearchfacet import supersearchfacet
    from click.testing import CliRunner
    result = CliRunner().invoke(supersearchfacet, ["--help"])
    cog.out("::\n\n")
    for line in result.output.splitlines():
        if line.strip():
            cog.out(f"   {line}\n")
        else:
            cog.out("\n")
    ]]]
::

   Usage: supersearchfacet [OPTIONS]

     Fetches facet data from Crash Stats using Super Search

     There are two ways to run this:

     First, you can specify Super Search API fields to generate the query.

     For example:

     $ supersearchfacet --product=Firefox --_facets=version

     Second, you can pass in a url from a Super Search on Crash Stats. This command
     will then pull out the parameters. You can override those parameters with
     command line arguments.

     $ supersearchfacet --supersearch-url='longurlhere' --_facets=version

     Make sure to use single quotes when specifying values so that your shell
     doesn't expand variables.

     You can only specify one facet using "--_facets". If you don't specify one, it
     defaults to "signature".

     By default, returned data is a tab-delimited table. Tabs and newlines in
     output is escaped. Use "--format" to specify a different output format.

     For list of available fields and Super Search API documentation, see:

     https://crash-stats.mozilla.org/documentation/supersearch/

     https://crash-stats.mozilla.org/documentation/supersearch/api/

     This generates a table values and counts. If you want values and counts over a
     series of days, use "--period=daily".

     This requires an API token in order to search and get results for protected
     data. Using an API token also reduces rate-limiting. Set the
     CRASHSTATS_API_TOKEN environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz supersearchfacet ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                     host for system to fetch facets from
     --supersearch-url TEXT          Super Search url to base query on
     --start-date TEXT               start date for range; YYYY-MM-DD format
     --end-date TEXT                 end date for range; YYYY-MM-DD format;
                                     defaults to today
     --relative-range TEXT           relative range ending on end-date
     --period [none|daily|hourly|weekly]
                                     period to facet on to get count/period
                                     [default: none]
     --format [table|tab|markdown|json]
                                     format to print output  [default: table]
     --verbose / --no-verbose        whether to print debugging output
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically
     --help                          Show this message and exit.
.. [[[end]]]

See the breakdown of crash reports by product for the last 7 days::

    $ supersearchfacet --_facets=product

See crashes broken down by product and down by day for the last 7 days::

    $ supersearchfacet --daily --relative-range=7d --_facets=product

See just Firefox crashes broken down by day for the last 14 days::

    $ supersearchfacet --daily --relative-range=14d --_facets=product --product=Firefox

Results are formatted as tab-delimited by default. Markdown and JSON output are
also available.

Get the table in Markdown for easy cut-and-paste into Markdown things::

    $ supersearchfacet --daily --format=markdown --relative-range=14d --_facets=product \
        --product=Firefox

See Super Search API documentation for details on notation and fields:

* https://crash-stats.mozilla.org/documentation/supersearch/
* https://crash-stats.mozilla.org/documentation/supersearch/api/


fetch-data
----------

.. [[[cog
    from crashstats_tools.cmd_fetch_data import fetch_data
    from click.testing import CliRunner
    result = CliRunner().invoke(fetch_data, ["--help"])
    cog.out("::\n\n")
    for line in result.output.splitlines():
        if line.strip():
            cog.out(f"   {line}\n")
        else:
            cog.out("\n")
    ]]]
::

   Usage: fetch-data [OPTIONS] OUTPUTDIR [CRASHIDS]...

     Fetches crash data from Crash Stats (https://crash-stats.mozilla.org/) system.

     Given one or more crash ids via command line or stdin (one per line), fetches
     crash data and puts it in specified directory.

     Crash data is split up into directories: raw_crash/, dump_names/,
     processed_crash/, and directories with the same name as the dump type.

     https://antenna.readthedocs.io/en/latest/overview.html#aws-s3-file-hierarchy

     This requires an API token in order to download dumps and protected data.
     Using an API token also reduces rate-limiting. Set the CRASHSTATS_API_TOKEN
     environment variable to your API token value:

     CRASHSTATS_API_TOKEN=xyz fetch-data crashdata ...

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Remember to abide by the data access policy when using data from Crash Stats!
     The policy is specified here:

     https://crash-stats.mozilla.org/documentation/protected_data_access/

   Options:
     --host TEXT                   host to pull crash data from; this needs to
                                   match CRASHSTATS_API_TOKEN value
     --overwrite / --no-overwrite  whether or not to overwrite existing data
     --raw / --no-raw              whether or not to save raw crash data
     --dumps / --no-dumps          whether or not to save dumps
     --processed / --no-processed  whether or not to save processed crash data
     --color / --no-color          whether or not to colorize output; note that
                                   color is shut off when stdout is not an
                                   interactive terminal automatically
     --help                        Show this message and exit.
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
    from click.testing import CliRunner
    result = CliRunner().invoke(reprocess, ["--help"])
    cog.out("::\n\n")
    for line in result.output.splitlines():
        if line.strip():
            cog.out(f"   {line}\n")
        else:
            cog.out("\n")
    ]]]
::

   Usage: reprocess [OPTIONS] [CRASHIDS]...

     Sends specified crashes for reprocessing

     This requires CRASHSTATS_API_TOKEN to be set in the environment to a valid API
     token.

     To create an API token for Crash Stats, visit:

     https://crash-stats.mozilla.org/api/tokens/

     Note: If you're processing more than 10,000 crashes, you should use a sleep
     value that balances the rate of crash ids being added to the queue and the
     rate of crash ids being processed. For example, you could use "--sleep 10"
     which will sleep for 10 seconds between submitting groups of crashes.

     Also, if you're processing a lot of crashes, you should let us know before you
     do it.

   Options:
     --host TEXT                     host for system to reprocess in  [default:
                                     https://crash-stats.mozilla.org]
     --sleep INTEGER                 how long in seconds to sleep before submitting
                                     the next group  [default: 1]
     --ruleset TEXT                  processor pipeline ruleset to use for
                                     reprocessing these crash ids
     --allow-many / --no-allow-many  don't prompt user about letting us know about
                                     reprocessing more than 10,000 crashes
     --color / --no-color            whether or not to colorize output; note that
                                     color is shut off when stdout is not an
                                     interactive terminal automatically
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


Prior art and related projects
==============================

https://github.com/mozilla/libmozdata
    Python library which has a ``Supersearch`` class for performing queries and
    a ``ProcessedCrash`` class for fetching processed crash data.

https://github.com/mozilla-services/socorro
    Socorro (the code base for Crash Stats) has a Docker-based local dev
    environment which includes a series of commands for manipulating data.

    https://socorro.readthedocs.io/en/latest/service/processor.html#processing-crashes
