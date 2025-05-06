
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.object_checks import check_stream_info, check_films_data_list, check_collection, has_keys
from tests.support.testutils import is_uuid

from unittest import TestCase
from unittest.mock import MagicMock

from codequick import Listitem

from resources.lib.ctree import ct_api
from resources.lib.ctree import ct_data


setUpModule = fixtures.setup_web_test


# noinspection PyMethodMayBeStatic
class FetchJsonp(TestCase):
    """Get some js documents from the web and check if they parse"""
    def test_fetch_films_en_documents(self):
        """Films in subscription"""
        resp = ct_api.get_jsonp('films-en-documentaires/payload.js')
        assert type(resp) is dict

    def test_fetch_huur_films(self):
        resp = ct_api.get_jsonp('films/payload.js')
        # with open('../experiments/films-payload.json', 'w') as f:
        #     json.dump(resp, f, indent=4)
        assert type(resp) is dict

    def test_fetch_specific_films(self):
        """Details of the film 'ema'"""
        resp = ct_api.get_jsonp('films/ema/payload.js')
        # with open('../experiments/film_details.json', 'w') as f:
        #     json.dump(resp, f, indent=4)
        assert type(resp) is dict

    def test_fetch_collections_films(self):
        """Details of the film 'ema'"""
        resp = ct_api.get_jsonp('films/ema/payload.js')
        # with open('../experiments/film_details.json', 'w') as f:
        #     json.dump(resp, f, indent=4)
        assert type(resp) is dict

    def test_fetch_cinetree_originals(self):
        resp = ct_api.get_jsonp('originals/payload.js')
        assert type(resp) is dict


# noinspection PyMethodMayBeStatic
class GetFilmUrls(TestCase):
    def test_get_urls_by_uuid(self):
        # To view films from the selected list, which have uuid
        url = ct_api.create_stream_info_url('c1321650-7394-4106-952d-e38872ab5f47', None)
        stream_info = ct_api.get_stream_info(url)
        check_stream_info(stream_info)
        # Morgen gaat het beter
        url = ct_api.create_stream_info_url('c1e7f9fd-43fa-41e7-ab54-a8f1bcda1e8f', None)
        stream_info = ct_api.get_stream_info(url)
        check_stream_info(stream_info)

    def test_get_urls_by_slug(self):
        # Films listed in month subscription do not have a key uuid, so are requested by their full_slug
        url = ct_api.create_stream_info_url(None, 'shorts/moffenmeid')
        stream_info = ct_api.get_stream_info(url)
        check_stream_info(stream_info)


class GetFilmsList(TestCase):
    # TODO: this more of an api test
    def test_create_film_list_collection_drama_fromweb(self):
        data = ct_api.get_jsonp('collecties/drama/payload.js')
        films = list(ct_data.create_films_list(data))
        self.assertGreater(len(films), 10)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item.data)


# noinspection PyMethodMayBeStatic
class GetCollections(TestCase):
    def test_get_preferred_collection_from_web(self):
        """Get the list of collections that the website presents on the page
        'huur films', which is only a small subset of all available collections

        """
        coll_list = ct_api.get_preferred_collections(page='films')
        for col in coll_list:
            check_collection(self, col)

    def test_get_all_collections_from_web(self):
        """Get the list of collections that the website calls 'all collections'.

        """
        coll_list = list(ct_api.get_collections())
        for col in coll_list:
            check_collection(self, col)

    def test_get_films_in_collection_cinetree_originals(self):
        coll_data = ct_api.get_jsonp('collecties/cinetree-originals/payload.js')
        film_list = list(ct_data.create_films_list(coll_data))
        for film in film_list:
            Listitem.from_dict(MagicMock(), **film.data)


# noinspection PyMethodMayBeStatic
class Gen(TestCase):
    def test_get_watched(self):
        result = ct_api.get_watched_films()
        for film in result:
            self.assertIsInstance(film, ct_data.FilmItem)
            self.assertTrue(film)

    def test_get_purchased(self):
        resp = ct_api.get_rented_films()
        check_films_data_list(resp, allow_none_values=False)

    def get_stream_info(self):
        # Get info of free film 'Intercepted'
        resp = ct_api.get_stream_info('https://api.cinetree.nl/films/d63ffb56-7fa3-4965-ba3c-03e95d7179b0')
        has_keys(resp, 'subtitles', 'url', 'watchHistoryId')

    def test_get_payment_info(self):
        amount, transaction = ct_api.get_payment_info('ef51ee02-0635-4547-a35d-d7844e0c5426')
        self.assertGreater(amount, 0.0)
        self.assertIsInstance(transaction, str)


class SearchFilm(TestCase):
    """A search on Cinetree returns a list of uuids of films that meet the search criteria.

    """
    def test_search_nothing(self):
        result = ct_api.search_films()
        self.assertListEqual(result, [])

    def test_search_title(self):
        result = ct_api.search_films(search_term='love')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0, "Search on 'love' returned an empty list")
        for film_uuid in result:
            is_uuid(film_uuid)
        # search something with no results.
        result = ct_api.search_films(search_term='nkm54l3m')
        self.assertListEqual(result, [])


    def test_search_genre(self):
        for genre in ct_api.GENRES:
            result = ct_api.search_films(genre=genre)
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0, "Genre '{}' returned an empty list".format(genre))
            for film_uuid in result:
                is_uuid(film_uuid)

    def test_search_country(self):
        """Only 2 character country codes are accepted, both upper, lower case and combinations"""
        result_1 = ct_api.search_films(country='NL')
        self.assertGreater(len(result_1), 0, "Country 'NL' returned an empty list")
        for film_uuid in result_1:
            is_uuid(film_uuid)
        result_2 = ct_api.search_films(country='Nl')
        self.assertListEqual(result_1, result_2)
        result_3 = ct_api.search_films(country='nl')
        self.assertListEqual(result_1, result_3)

    def test_search_duration(self):
        result = ct_api.search_films(duration=60)
        self.assertGreater(len(result), 1)
        for film_uuid in result:
            is_uuid(film_uuid)
        result = ct_api.search_films(duration=120)
        self.assertGreater(len(result), 1)
        for film_uuid in result:
            is_uuid(film_uuid)
        result = ct_api.search_films(duration=500)
        self.assertGreater(len(result), 1)
        for film_uuid in result:
            is_uuid(film_uuid)
        # Any other value is invalid
        self.assertRaises(KeyError, ct_api.search_films, duration=30)
        self.assertRaises(KeyError, ct_api.search_films, duration=59)
        self.assertRaises(KeyError, ct_api.search_films, duration=61)
        self.assertRaises(KeyError, ct_api.search_films, duration=119)
        self.assertRaises(KeyError, ct_api.search_films, duration=121)
