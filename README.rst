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
:Slack: ``#breakpad`` on Mozilla Slack
:Community Participation Guidelines: `Guidelines <https://github.com/mozilla-services/antenna/blob/master/CODE_OF_CONDUCT.md>`_


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

Perform Super Search queries on Crash Stats.

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

Performs facets and daily-facets.

See the breakdown of crash reports by product for the last 7 days::

    $ supersearchfacet --_facets=product

See crashes broken down by product and down by day for the last 7 days::

    $ supersearchfacet --daily --relative-range=7d --_facets=product

See just Firefox crashes broken down by day for the last 14 days::

    $ supersearchfacet --daily --relative-range=14d --_facets=product --product=Firefox

Results are formatted as tab-delimited by default. Markdown and JSON output are
also available.

Get the table in Markdown for easy cut-and-paste into Markdown things::

    $ supersearchfacet --daily --format=markdown --relative-range=14d --_facets=product --product=Firefox

See Super Search API documentation for details on notation and fields:

* https://crash-stats.mozilla.org/documentation/supersearch/
* https://crash-stats.mozilla.org/documentation/supersearch/api/


fetch-data
----------

Fetch data for specified crash reports.

This lets you download raw crash, dumps, and processed crash from Crash Stats.

Fetch processed crash data for specific crash id::

    $ fetch-data --no-raw --no-dumps --processed 723cacd6-1684-420e-a1c7-f04240190731

Fetch raw crash data using supersearch command to generate crash ids::

    $ supersearch --product=Firefox --num=10 | \
        fetch-data --raw --no-dumps --no-processed crashdir


reprocess
---------

Let's you specify crash reports for reprocessing.

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

    $ supersearch --date=">=2019-07-30" --date='<2019-07-31' --dom_fission_enabled='!__null__'


Example 4
---------

I want to see number of crash reports for the last 14 days broken down by day
and by product where ``DOMFissionEnabled`` exists in the crash report.

I would do this::

    $ supersearchfacet --daily --format=markdown --relative-range=14d --dom_fission_enabled='!__null__' --_facets=product


Prior art and related projects
==============================

https://github.com/mozilla/libmozdata
    Python library which has a ``Supersearch`` class for performing queries and
    a ``ProcessedCrash`` class for fetching processed crash data.

https://github.com/mozilla-services/socorro
    Socorro (the code base for Crash Stats) has a Docker-based local dev
    environment which includes a series of commands for manipulating data.

    https://socorro.readthedocs.io/en/latest/service/processor.html#processing-crashes


Release process
===============

1. Create branch
2. Update version and release date in ``crashstats_tools/__init__.py``
3. Update ``HISTORY.rst``
4. Push the branch, create a PR, review it, merge it
5. Create a signed tag, push to github::

     git tag -s v0.1.0
     git push --tags REMOTE TAGNAME

6. Build::

     python setup.py sdist bdist_wheel

   Make sure to use Python 3 with an updates ``requirements-dev.txt``.

7. Upload to PyPI::

     twine upload dist/*
