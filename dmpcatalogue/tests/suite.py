# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import sys
import unittest


def _run_tests(test_suite, package_name):
    count = test_suite.countTestCases()
    print("########")
    print(f"{count} test(s) has been discovered in {package_name}")
    print("########")

    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(test_suite)


def test_all(package="."):
    test_loader = unittest.defaultTestLoader
    test_suite = test_loader.discover(package)
    _run_tests(test_suite, package)


if __name__ == "__main__":
    test_all()
