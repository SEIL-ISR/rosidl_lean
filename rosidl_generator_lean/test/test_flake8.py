"""Run the ament flake8 configuration over this package's Python."""

import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    ament_flake8 = pytest.importorskip('ament_flake8.main')
    rc, errors = ament_flake8.main_with_errors(argv=[])
    assert rc == 0, \
        'Found %d code style errors / warnings:\n' % len(errors) + \
        '\n'.join(errors)
