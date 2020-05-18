# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from click.testing import CliRunner

from crashstats_tools import cmd_reprocess


def test_it_runs():
    runner = CliRunner()
    result = runner.invoke(cmd_reprocess.reprocess, ["--help"])
    assert result.exit_code == 0
