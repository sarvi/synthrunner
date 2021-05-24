"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""

from sys import argv


def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        user_cmd = argv[1]
        if user_cmd == 'install':
            print('install subcommand')
        else:
            RuntimeError('please supply a command for synthrunner - e.g. install.')  # noqa: E501
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
