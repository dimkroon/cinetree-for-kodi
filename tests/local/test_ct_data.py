
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import datetime
import itertools
import time
from urllib.parse import quote_plus
from copy import deepcopy

from unittest import TestCase
from unittest.mock import MagicMock

from tests.support import fixtures
fixtures.global_setup()

from codequick import Listitem

from tests.support.testutils import open_jsonp, open_json
from tests.support.object_checks import check_collection, has_keys

from resources.lib.ctree import ct_data


# noinspection PyMethodMayBeStatic
class CreateFilmItem(TestCase):
    def test_create_invalid_item(self):
        self.assertIsNone(ct_data.create_film_item(None))
        self.assertIsNone(ct_data.create_film_item(''))
        self.assertIsNone(ct_data.create_film_item({}))
        self.assertIsNone(ct_data.create_film_item({'a': 1}))

    def test_create_film_item(self):
        item_data = ct_data.create_film_item({'content': {}})
        has_keys(item_data, 'label', 'art', 'info', 'params')
        has_keys(item_data['params'], 'title', 'slug', 'end_date')

    def test_end_date(self):
        # date in the future
        item_data = ct_data.create_film_item({'content': {'endDate': '2060-01-01 00:00'}})
        self.assertIsInstance(item_data, dict)
        # date in the past
        self.assertIsNone(ct_data.create_film_item({'content': {'endDate': '2021-04-22 00:00'}}))
        # date in other format is rejected
        self.assertIsNone(ct_data.create_film_item({'content': {'endDate': '2060-04-22'}}))
        self.assertIsNone(ct_data.create_film_item({'content': {'endDate': '22-04-2022 00:00'}}))

    def test_show_subscription_availability(self):
        """If subscription films reach the end date a notification is added to the title"""
        now = datetime.datetime.utcnow()
        item_data = ct_data.create_film_item({'content': {'svodEndDate': '2060-01-01 00:00', 'title': ''}})
        self.assertEqual('', item_data['info']['plot'])

        end_date = now + datetime.timedelta(hours=4)
        item_data = ct_data.create_film_item({'content': {'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}})
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        end_date = now + datetime.timedelta(days=1)
        item_data = ct_data.create_film_item({'content': {'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}})
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        end_date = now + datetime.timedelta(days=10)
        item_data = ct_data.create_film_item({'content': {'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}})
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        # No message added when film is still more than 10 days available
        end_date = now + datetime.timedelta(days=11)
        item_data = ct_data.create_film_item({'content': {'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}})
        self.assertTrue("" in item_data['info']['title'])   # localized strings return '' in tests

    def test_show_price(self):
        """Price should only be added to plot if the film is curently not within the subscription plan.
        """
        item_data = ct_data.create_film_item({'content': {'tvodPrice': '499'}})
        self.assertEqual('\n\n[B]€ 4,99[/B]', item_data['info']['plot'])
        # do not show price on films in monthly subscription (i.e. svodEndDate is in the future)
        item_data = ct_data.create_film_item({'content': {'tvodPrice': '499', 'svodEndDate': '2060-01-01 00:00', 'title': ''}})
        self.assertEqual('', item_data['info']['plot'])


class GetFilmsList(TestCase):
    def test_create_film_list_storyblok(self):
        sb_films = itertools.islice(open_json('st_blok/films.json').values(), 4)
        films = ct_data.create_films_list(sb_films, 'storyblok')
        self.assertEqual(len(films), 4)

    def test_create_film_list_suggested(self):
        data = open_jsonp('films_en_docus-payload.js')
        films = ct_data.create_films_list(data, 'recommended')
        self.assertLessEqual(len(films), 4)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item)

    def test_create_film_list_subscription(self):
        data = open_jsonp('films_en_docus-payload.js')
        films = ct_data.create_films_list(data, 'subscription')
        self.assertGreater(len(films), 10)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item)

    def test_create_film_list_collection_drama(self):
        data = open_jsonp('collecties-drama-payload.js')
        films = ct_data.create_films_list(data)
        self.assertGreater(len(films), 10)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item)

    def test_create_film_with_invalid_data(self):
        data = open_jsonp('films_en_docus-payload.js')
        self.assertRaises(ValueError, ct_data.create_films_list, data, 'something')     # unknown list type
        data = {'some': 'dict'}
        self.assertRaises(ValueError, ct_data.create_films_list, data)              # invalid data


# noinspection PyMethodMayBeStatic
class Collections(TestCase):
    def test_create_collection_items(self):
        data = open_jsonp('collecties-payload.js')
        for col in data['data'][0]['collections']:
            col_dict = ct_data.create_collection_item(col)
            check_collection(self, col_dict)

    def test_create_film_list_from_a_collection(self):
        coll_data = open_jsonp('collecties-cinetree-originals-payload.js')
        film_list = list(ct_data.create_films_list(coll_data))
        for film in film_list:
            Listitem.from_dict(MagicMock(), **film)


class SelectTrailerUrl(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.orig_trailer = {'selected': '1234abcd', "plugin": "cinetree-autocomplete"}
        cls.vimeo_url = 'https://vimeo'
        cls.orig_url = 'https://youtube'
        cls.expect_vimeo = 'plugin://plugin.video.cinetree/resources/lib/main/play_trailer?url=https%3A%2F%2Fvimeo'
        cls.expect_youtube = 'plugin://plugin.video.cinetree/resources/lib/main/play_trailer?url=https%3A%2F%2Fyoutube'
        # noinspection PyUnresolvedReferences
        cls.expect_cinetree = 'plugin://plugin.video.cinetree/resources/lib/main/play_trailer?url=' \
                              + quote_plus('https://api.cinetree.nl/videos/vaem/' + cls.orig_trailer['selected'])

    def setUp(self) -> None:
        self.film_data = deepcopy({
            'originalTrailer': self.orig_trailer,
            'trailerVimeoURL': self.vimeo_url,
            'originalTrailerURL': self.orig_url})

    def test_prefer_vimeo_all_present(self):
        trailer = ct_data._select_trailer_url(self.film_data, False)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_vimeo_but_vimeo_not_present(self):
        self.film_data.pop('trailerVimeoURL')
        trailer = ct_data._select_trailer_url(self.film_data, False)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_vimeo_but_vimeo_is_empty_string(self):
        self.film_data['trailerVimeoURL'] = ''
        trailer = ct_data._select_trailer_url(self.film_data, False)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_vimeo_but_vimeo_is_empty_string_and_originalTrailer_not_present(self):
        film_data = {'trailerVimeoURL': '', 'originalTrailerURL': self.orig_url}
        trailer = ct_data._select_trailer_url(film_data, False)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_vimeo_but_vimeo_is_absent_and_originalTrailer_selected_is_None(self):
        film_data = {'originalTrailer': {'selected': None, "plugin": "cinetree-autocomplete"},
                     'originalTrailerURL': self.orig_url}
        trailer = ct_data._select_trailer_url(film_data, False)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_vimeo_but_vimeo_is_absent_and_originalTrailer_plugin_is_wrong_type(self):
        film_data = {'originalTrailer': {'selected': '1234abcd', "plugin": "autocomplete"},
                     'originalTrailerURL': self.orig_url}
        trailer = ct_data._select_trailer_url(film_data, False)
        self.assertEqual('', trailer)

    def test_prefer_original_all_present(self):
        trailer = ct_data._select_trailer_url(self.film_data, True)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_original_but_originalTrailer_not_present(self):
        self.film_data.pop('originalTrailer')
        trailer = ct_data._select_trailer_url(self.film_data, True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_absent_and_originalUrl_empty(self):
        film_data = {'trailerVimeoURL': self.vimeo_url, 'originalTrailerURL': ''}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_original_but_both_originalTrailer_and_originalUrl_absent(self):
        film_data = {'trailerVimeoURL': self.vimeo_url}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_whitspace_in_url(self):
        film_data = {'trailerVimeoURL': ' ' + self.vimeo_url}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_vimeo, trailer)

        film_data = {'trailerVimeoURL': self.vimeo_url + ' '}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_vimeo, trailer)

        film_data = {'originalTrailerURL': ' ' + self.orig_url + ' '}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_selected_is_None(self):
        # noinspection PyTypedDict
        self.film_data['originalTrailer']['selected'] = None
        trailer = ct_data._select_trailer_url(self.film_data, True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_selected_is_None_and_originalUrl_is_empty(self):
        film_data = {'originalTrailer': {'selected': None, "plugin": "cinetree-autocomplete"},
                     'trailerVimeoURL': self.vimeo_url, 'originalTrailerURL': ''}
        trailer = ct_data._select_trailer_url(film_data, True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_original_but_originalTrailer_plugin_is_wrong_type(self):
        self.film_data['originalTrailer']['plugin'] = "autocomplete"
        trailer = ct_data._select_trailer_url(self.film_data, True)
        self.assertEqual('', trailer)

    def test_no_trailers_present(self):
        self.assertEqual('', ct_data._select_trailer_url({}, True))
        self.assertEqual('', ct_data._select_trailer_url({}, False))

    def test_all_trailers_are_empty_strings(self):
        film_data = {'trailerVimeoURL': '', 'originalTrailerURL': ''}
        self.assertEqual('', ct_data._select_trailer_url(film_data, True))
        self.assertEqual('', ct_data._select_trailer_url(film_data, False))

    def test_invalid_trailer_data(self):
        """The function should fail silently and just return an empty string
        """
        # First ensure the original trailer is returned on valid data
        self.assertEqual(self.expect_cinetree, ct_data._select_trailer_url(self.film_data, True))

        del self.film_data['originalTrailer']['plugin']
        self.assertEqual('', ct_data._select_trailer_url(self.film_data, True))
        # noinspection PyTypedDict
        self.film_data['originalTrailer'] = "https://some.trailer.com"
        self.assertEqual('', ct_data._select_trailer_url(self.film_data, True))


class Generic(TestCase):
    def test_list_from_items_string(self):
        # noinspection PyTypeChecker
        self.assertEqual(None, ct_data.list_from_items_string(None))
        self.assertEqual(None, ct_data.list_from_items_string(''))
        self.assertEqual(["bla"], ct_data.list_from_items_string('bla'))
        self.assertEqual(['bli', ' bla', ' blob'], ct_data.list_from_items_string('bli, bla, blob'))
