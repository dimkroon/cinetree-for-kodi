
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import unittest
from unittest.mock import MagicMock

from codequick import Listitem
from resources.lib import main


setUpModule = fixtures.setup_web_test


class MainTest(unittest.TestCase):
    def test_root(self):
        NUM_MAIN_MNU_ITEMS = 6
        items = list(main.root(MagicMock()))
        self.assertEqual(NUM_MAIN_MNU_ITEMS, len(items),
                         "Expected {} items in main menu, got {}".format(NUM_MAIN_MNU_ITEMS, len(items)))
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_mijn_films(self):
        items = list(main.list_my_films(MagicMock()))
        for item in items:
            self.assertIsInstance(item, Listitem)
        self.assertGreater(len(items), 1)

        items = list(main.list_my_films(MagicMock(), 'finished'))
        for item in items:
            if item is False:
                # If there are no items the list should contain one single False
                self.assertEqual(1, len(items))
            else:
                self.assertIsInstance(item, (Listitem, type(False)))

        items = list(main.list_my_films(MagicMock(), 'purchased'))
        for item in items:
            if item is False:
                # If there are no items the list should contain one single False
                self.assertEqual(1, len(items))
            else:
                self.assertIsInstance(item, (Listitem, type(False)))

    def test_list_films_and_docus_deze_maand(self):
        items = list(main.list_films_and_docus(MagicMock(), category='subscription'))
        self.assertAlmostEqual(20, len(items), delta=4)
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_list_rental_collections(self):
        items = list(main.list_rental_collections(MagicMock()))
        self.assertAlmostEqual(10, len(items), delta=2)
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_search(self):
        items = list(main.do_search(MagicMock, search_query='love'))
        for item in items:
            self.assertIsInstance(item, Listitem)
        # search something with no results.
        result = main.do_search(MagicMock, search_query='nkm54l3m')
        self.assertIsInstance(result, type(False))

    def test_play_film_from_uuid(self):
        # Using uuid of gratis film 'Woman at war', so it can be played with every type of account.
        playitem = main.play_film(MagicMock(), '', 'aa97748e-1981-4f34-80fe-5846756908fa', None)
        self.assertIsInstance(playitem, Listitem)

    def test_list_genre_drama(self):
        """As there are a lot of film in genre drama, only the maximum of 50 per page ar returned."""
        items = list(main.list_films_by_genre(MagicMock(), genre='drama'))
        self.assertAlmostEqual(51, len(items), delta=10)       # some films can be filtered out on expired endDate
        self.assertLessEqual(len(items), 51)
