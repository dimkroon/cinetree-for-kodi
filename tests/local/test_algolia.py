# ------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------
from codequick.utils import unicode_type

from tests.support import fixtures
fixtures.global_setup()

import json
import unittest
from unittest.mock import patch
from requests import exceptions

from resources.lib import algolia
from tests.support.testutils import HttpResponse, open_doc

setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


@patch('resources.lib.storyblok.requests.post',
       return_value=HttpResponse(content=open_doc('algolia/search.json')().encode()))
class AlgoliaSearch(unittest.TestCase):
    def test_search(self, _):
        results = algolia.search('war')
        self.assertIsInstance(results, list)

    def test_empty_search_term(self, _):
        results = algolia.search('')
        self.assertListEqual([], results)
        results = algolia.search(None)
        self.assertListEqual([], results)