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
:Status: Alpha
:Community Participation Guidelines: `Guidelines <https://github.com/mozilla-services/antenna/blob/master/CODE_OF_CONDUCT.md>`_


Installing
==========

crashstats-tools is available on `PyPI <https://pypi.org>`_. You can install it
with::

    $ pip install crashstats-tools


Support
=======

This is an alpha-quality project that I spent some time on because it seemed
helpful. If you have any problems, please write up an issue in the issue
tracker and I'll get to it when I'm able.


Tools
=====

supersearch
-----------

Perform Super Search queries on Crash Stats.

Fetch 10 crash ids for Firefox::

    $ supersearch --num=10 --product=Firefox

Fetch 57 crash ids that match a Super Search query::

    $ supersearch --num=57 --supersearch-url="https://crash-stats.mozilla.org/search/?release_channel=nightly&version=70.0a1&product=Firefox&_sort=-date"

Fetch uuid, product, version, and build_id for crash reports that have "OOM" in
the signature::

    $ supersearch --_columns=uuid --_columns=product --_columns=version \
        --_columns=build_id --signature="~OOM"

Results are formatted as tab-delimited by default. JSON output is also
available.

Note that this doesn't support Super Search aggregations.

See Super Search API details:

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


API token
=========

You need to use a API token to:

* download data containing personally identifiable information
* download security sensitive data
* get out from the shadow of extreme API use rate limiting

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

    $ supersearch --date=">=2019-07-30" --date="<2019-07-31" --dom_fission_enabled="!__null__"


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
