=============
crashstats-tools
=============

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


Tools
=====

fetch-crashids
--------------

Fetch a list of crash ids for crash reports based on various criteria.

Fetch 10 recent crash ids for Firefox::

    $ fetch-crashids --num=10 --product=Firefox

Fetch 100 crash ids that match a Supersearch query::

    $ fetch-crashids --num=100 --url="https://crash-stats.mozilla.org/search/?release_channel=nightly&version=70.0a1&product=Firefox&_sort=-date"


fetch-data
----------

Fetch data for specified crash reports.

This lets you download raw crash, dumps, and processed crash from Crash Stats.


API token
=========

You need to use a API token to:

* download data containing personally identifiable information,
* download security sensitive data,
* get out from the shadow of extreme API use rate limiting

If you have access, you can generate an API token here:

https://crash-stats.mozilla.org/api/tokens/

Once you have acquired one, set the ``CRASHSTATS_API_TOKEN`` environment
variable when using crashstats-tools commands.


Use cases
=========

These tools are helpful when downloading data for analysis as well as
downloading data to test other tools with.

Say I want to do some analysis on data in registers for crash reports that have
the signature "OOM | small".

The registers are in the ``json_dump`` field of the processed crash. I don't
need the raw crash or the dumps.

I'm going to put all the crash data in ``crashdata/`` to analyze it.

I would do something like this::

    $ mkdir crashdata
    $ fetch-crashids --product=Firefox --signature="OOM | small" --num=1000 | \
        fetch-data --no-raw --no-dumps --processed crashdata

Then I run whatever analysis scripts I have on the processed crash data.


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
