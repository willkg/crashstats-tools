=======
History
=======

1.1.0 (May 21, 2020)
====================

Features:

* Rewrite commands to use click instead of argparse for argument parsing (#17)
* Add ``supersearchfacet`` command (#2)


1.0.4 (January 7, 2020)
=======================

Features:

* Add support for CRASHID, bp-CRASHID, and
  https://crash-stats.mozilla.org/report/index/CRASHID formats of crash id in
  reprocess and fetch_data commands
* Add tests for utils functions (#1)


1.0.3 (October 23rd, 2019)
==========================

Bugs:

* Handle HTTP 400 errors better so the user sees the error message
  in the HTTP response.
* Change examples to use single-quote which won't expand things in
  the shell.
* Redo the prompt when reprocessing > 10,000 crash reports.
* Fix the aggregation argument check.
* Remove IRC channel references--we don't use IRC anymore.


1.0.2 (August 22nd, 2019)
=========================

Features:

* add reprocess command (#4)


1.0.1 (July 31st, 2019)
=======================

Bugs:

* fix saving ``dump_names``


1.0.0 (July 31st, 2019)
=======================

Initial writing.

* project scaffolding
* supersearch command
* fetch-data command
