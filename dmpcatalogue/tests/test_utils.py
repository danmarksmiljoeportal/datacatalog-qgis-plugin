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

import os
import shutil
from datetime import datetime, timedelta

from qgis.testing import start_app, unittest

from dmpcatalogue.core.utils import cache_directory, file_exists


class test_utils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_app()

    def test_cache_directory(self):
        cache_dir = cache_directory("test_cache")
        self.assertTrue(os.path.exists(cache_dir))
        head, tail = os.path.split(cache_dir)
        self.assertEqual(tail, "test_cache")

        cache_dir2 = cache_directory("test_cache")
        self.assertTrue(os.path.exists(cache_dir2))
        head, tail = os.path.split(cache_dir)
        self.assertEqual(tail, "test_cache")

        self.assertEqual(cache_dir, cache_dir2)

        shutil.rmtree(cache_dir)

    def test_file_exists(self):
        cache_dir = cache_directory("test_cache")
        self.assertTrue(os.path.exists(cache_dir))

        file_name = os.path.join(cache_dir, "file.txt")
        self.assertFalse(os.path.exists(file_name))
        self.assertFalse(file_exists(file_name))

        with open(file_name, "w", encoding="utf-8") as f:
            f.write("test")

        self.assertTrue(os.path.exists(file_name))
        self.assertTrue(file_exists(file_name))
        self.assertFalse(file_exists(file_name, -1))

        now = datetime.now()
        # set date to 1 day ago from now
        new_date = now - timedelta(days=1)
        os.utime(file_name, (new_date.timestamp(), new_date.timestamp()))
        # by default file is outdated
        self.assertFalse(file_exists(file_name))
        # file is valid, as it should be one or more days older
        self.assertTrue(file_exists(file_name, 1))
        self.assertTrue(file_exists(file_name, 2))

        # set date to 2 days ago from now
        new_date = now - timedelta(days=2)
        os.utime(file_name, (new_date.timestamp(), new_date.timestamp()))
        # file is outdated, as it should be no more than 1 day older
        self.assertFalse(file_exists(file_name))
        self.assertFalse(file_exists(file_name, 1))
        # file is valid, as it should be two or more days older
        self.assertTrue(file_exists(file_name, 2))
        self.assertTrue(file_exists(file_name, 3))

        shutil.rmtree(cache_dir)
