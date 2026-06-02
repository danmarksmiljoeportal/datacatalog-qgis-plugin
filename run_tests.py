#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run tests
from dmpcatalogue.tests.suite import test_all
test_all()
