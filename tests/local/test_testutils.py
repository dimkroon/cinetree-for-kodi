

# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.testutils import get_sb_film

import unittest


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class GetTestSbFilm(unittest.TestCase):
    def test_get_single_film_by_uuid(self):
        result, num_items = get_sb_film('235dda06-abc6-4cce-8c91-8db94cc804f2')
        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))
        self.assertEqual(1, num_items)

    def test_get_multiple_films_by_uuid(self):
        result, num_items = get_sb_film(('235dda06-abc6-4cce-8c91-8db94cc804f2', '74eaf292-e10d-4e3d-aa5d-1872d6a8117c',
                                         '568c0171-c90f-4675-a040-ad5416c3fdcd', 'a7b26cda-ce86-4c74-8486-45a4465f15a5'))
        self.assertIsInstance(result, list)
        self.assertEqual(4, len(result))
        self.assertEqual(4, num_items)

    def test_get_films_by_genre(self):
        result, num_items = get_sb_film(genre='thriller')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 10)

    def test_get_films_per_page(self):
        # check how many films are present
        total = len(get_sb_film(genre='drama')[0])
        # retrieve all per page of 50 items
        page = 1
        films = []
        result, new_total = get_sb_film(genre='drama', page=page, items_per_page=50)
        self.assertEqual(total, new_total)
        while result:
            films.extend(result)
            page += 1
            result, _ = get_sb_film(genre='drama', page=page, items_per_page=50)
        # check if we have all items
        self.assertEqual(total, len(films))
