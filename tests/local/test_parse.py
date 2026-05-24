# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2026 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.testutils import open_nuxt3_json

from unittest import TestCase

from resources.lib import errors
from resources.lib import nuxt3


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class ParseNuxtJson(TestCase):
    def check_recommended_films_data_structure(self, film_list):
        """A list of recommended films has less info than the full list.
        """
        self.assertIsInstance(film_list, list)
        film_keys = {'startDate', 'endDate', 'background', 'title', 'genre', 'duration',
                     'kijkwijzer'}
        for film in film_list:
            self.assertIsInstance(film, dict)
            self.assertTrue('full_slug' in film.keys())
            content = film['content']
            self.assertEqual(film_keys, set(content.keys()).intersection(film_keys))

    def test__parse_collecties_payload(self):
        """Returns data containing a list of all available collections, within each collection a list
        of uuid's of films available in that collection

        """
        result = open_nuxt3_json('collecties-_payload.json')
        self.assertIsInstance(result, dict)
        col_list = result['collections-/collecties']
        col_keys = {'name', 'id', 'uuid', 'content', 'full_slug'}
        content_keys = {'image', 'description', 'films'}
        for collection in col_list:
            self.assertEqual(col_keys, set(collection.keys()).intersection(col_keys))
            self.assertEqual(content_keys, set(collection['content'].keys()).intersection(content_keys))

    def test__parse_films_payload(self):
        """A list of 8 collections with in each collection a list of films.
        Some collections are not found in 'all collections', like serie 'We Are Who We Are'
        These are the collection that are initially shown on the website.
        """
        result = open_nuxt3_json('films-_payload.json')
        self.assertIsInstance(result, dict)

    def test__parse_details_of_a_single_film(self):
        result = open_nuxt3_json('films-ema-_payload.json')
        self.assertIsInstance(result, dict)

    def test_parse_empty_document(self):
        self.assertRaises(errors.ParseError, nuxt3.parse, "")

    def test_parse_none_object(self):
        self.assertRaises(errors.ParseError, nuxt3.parse, None)
