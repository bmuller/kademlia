from glob import glob

import pycodestyle

from pylint import epylint as lint
import pytest

# skip these file tests till later
pytestmark = pytest.mark.skip


class LintError(Exception):
    pass


class TestCodeLinting:
    # pylint: disable=no-self-use
    def test_pylint(self):
        (stdout, _) = lint.py_run('kademlia', return_std=True)
        errors = stdout.read()
        if errors.strip():
            raise LintError(errors)

    # pylint: disable=no-self-use
    def test_pep8(self):
        style = pycodestyle.StyleGuide()
        files = glob('kademlia/**/*.py', recursive=True)
        result = style.check_files(files)
        if result.total_errors > 0:
            raise LintError("Code style errors found.")
