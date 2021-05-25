"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""

import locust.main

def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        locust.main.main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
