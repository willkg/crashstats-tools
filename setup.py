#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import codecs
import os
import re

from setuptools import find_packages, setup


def get_long_desc():
    return codecs.open("README.rst", encoding="utf-8").read()


def get_version():
    fn = os.path.join("src", "crashstats_tools", "__init__.py")
    vsre = r"""^__version__ = ['"]([^'"]*)['"]"""
    version_file = codecs.open(fn, mode="r", encoding="utf-8").read()
    return re.search(vsre, version_file, re.M).group(1)


INSTALL_REQUIRES = ["click", "more_itertools", "requests", "rich"]

EXTRAS_REQUIRE = {
    "dev": [
        "black==22.6.0",
        "build==0.8.0",
        "check-manifest==0.48",
        "flake8==4.0.1",
        "freezegun==1.2.1",
        "pytest==7.1.2",
        "responses==0.21.0",
        "tox==3.25.0",
        "tox-gh-actions==2.9.1",
        "twine==4.0.1",
        "wheel==0.37.1",
    ]
}


setup(
    name="crashstats-tools",
    version=get_version(),
    description="Tools for working with Crash Stats (https://crash-stats.mozilla.org/)",
    long_description=get_long_desc(),
    maintainer="Will Kahn-Greene",
    maintainer_email="willkg@mozilla.com",
    url="https://github.com/willkg/crashstats-tools",
    license="Mozilla Public License v2",
    include_package_data=True,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.7",
    entry_points="""
        [console_scripts]
        fetch-data=crashstats_tools.cmd_fetch_data:fetch_data
        reprocess=crashstats_tools.cmd_reprocess:reprocess
        supersearch=crashstats_tools.cmd_supersearch:supersearch
        supersearchfacet=crashstats_tools.cmd_supersearchfacet:supersearchfacet
    """,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.111",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
