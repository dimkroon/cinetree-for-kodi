
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.testutils import open_jsonp, doc_path
from tests.support.object_checks import check_films_data_list

from unittest import TestCase

from resources.lib import errors
from resources.lib import jsonp


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class ParseNuxtJsonp(TestCase):
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

    def test__parse_films_en_docus_state(self):
        result = open_jsonp('films_en_docus-state.js')
        self.assertIsInstance(result, dict)

    def test__parse_films_en_docus_payload(self):
        result = open_jsonp('films_en_docus-payload.js')
        # films and docu's has usually 2 listings of films; one with a few recommended films and another with al films
        film_lists = sorted([v['films'] for k, v in result['fetch'].items() if k.startswith('data-')], key=len)
        # noinspection PyTypeChecker
        self.check_recommended_films_data_structure(film_lists[0])
        check_films_data_list(film_lists[1], ('svodEndDate', ))

    def test__parse_collecties_drama_payload(self):
        result = open_jsonp('collecties-drama-payload.js')
        content = result['data'][0]['story']['content']
        self.assertIsInstance(content, dict)
        films = content['films']
        check_films_data_list(films, ('tvodPrice', 'tvodSubscribersPrice'))

    def test__parse_collecties_cinetree_originals_payload(self):
        result = open_jsonp('collecties-cinetree-originals-payload.js')
        content = result['data'][0]['story']['content']
        self.assertIsInstance(content, dict)
        check_films_data_list(content['films'], ('tvodPrice', 'tvodSubscribersPrice'))
        check_films_data_list(content['shorts'], ('tvodPrice', 'tvodSubscribersPrice'))

    def test__parse_collecties_prijswinnars_payload(self):
        result = open_jsonp('collecties-prijswinnaars-payload.js')
        self.assertIsInstance(result, dict)
        content = result['data'][0]['story']['content']
        check_films_data_list(content['films'], ('tvodPrice', 'tvodSubscribersPrice'))

    def test__parse_collecties_de_grote_winnars(self):
        result = open_jsonp('collecties-de-grote-winnaars-payload.js')
        content = result['data'][0]['story']['content']
        self.assertIsInstance(content, dict)
        check_films_data_list(content['films'], ('tvodPrice', 'tvodSubscribersPrice'))

    def test__parse_collecties_voor_een_glimlach_payload(self):
        result = open_jsonp('collecties-voor_een_glimlach-payload.js')
        content = result['data'][0]['story']['content']
        self.assertIsInstance(content, dict)
        check_films_data_list(content['films'], ('tvodPrice', 'tvodSubscribersPrice'))
        check_films_data_list(content['shorts'], ('tvodPrice', 'tvodSubscribersPrice'))

    def test__parse_collecties_payload(self):
        """Returns data containing a list of all available collections, within each collection a list
        of uuid's of films available in that collection

        """
        result = open_jsonp('collecties-payload.js')
        self.assertIsInstance(result, dict)
        col_list = result['data'][0]['collections']
        col_keys = {'name', 'id', 'uuid', 'content', 'full_slug'}
        content_keys = {'image', 'description', 'films'}
        for collection in col_list:
            self.assertEqual(col_keys, set(collection.keys()).intersection(col_keys))
            self.assertEqual(content_keys, set(collection['content'].keys()).intersection(content_keys))

    def test__parse_collecties_state(self):
        result = open_jsonp('collecties-state.js')
        self.assertIsInstance(result, dict)

    def test__parse_films_payload(self):
        """A list of 8 collections with in each collection a list of films.
        Some collections are not found in 'all collections', like serie 'We Are Who We Are'
        These are the collection that are initially shown on the website.
        """
        result = open_jsonp('films-payload.js')
        self.assertIsInstance(result, dict)

    def test__parse_details_of_a_single_film(self):
        result = open_jsonp('films_el-sicatio_room_164-payload.js')
        self.assertIsInstance(result, dict)
        result = open_jsonp('films-ema-payload.js')
        self.assertIsInstance(result, dict)

    def test_parse_empty_document(self):
        self.assertRaises(errors.ParseError, jsonp.parse, "")

    def test_parse_none_object(self):
        self.assertRaises(errors.ParseError, jsonp.parse, None)


class ParseSimpleJsonp(TestCase):
    def test_manifest(self):
        with open(doc_path('manifest.js'), 'r') as f:
            content = f.read()
        result = jsonp.parse_simple(content)
        self.assertIsInstance(result, dict)

    def test_empty_doc(self):
        result = jsonp.parse_simple("")
        self.assertIsInstance(result, dict)
        self.assertFalse(result)

    def test_parse_none_object(self):
        self.assertRaises(errors.ParseError, jsonp.parse_simple, None)
