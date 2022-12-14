

# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.object_checks import check_stream_info, check_films_data_list, check_collection
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


# noinspection PyMethodMayBeStatic
class GetFilmUrls(TestCase):
    def test_get_urls_maand_abo_selected(self):
        # To view films from the selected list have uuid
        url = ct_api.create_stream_info_url('7a88224a-370e-4c0b-9330-730ca74d6b39', None)
        stream_info = ct_api.get_stream_info(url)
        check_stream_info(stream_info)

    def test_get_urls_maand_abo(self):
        # Films listed in month subscription do not have a key uuid, so are requested by their full_slug
        url = ct_api.create_stream_info_url(None, 'films/kapsalon-romy')
        stream_info = ct_api.get_stream_info(url)
        check_stream_info(stream_info)


class GetFilmsList(TestCase):
    # TODO: this more of an api test
    def test_create_film_list_subscription_from_web(self):
        data = ct_api.get_jsonp('films-en-documentaires/payload.js')
        films = list(ct_data.create_films_list(data, 'subscription'))
        self.assertGreater(len(films), 10)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item)

    # TODO: this more of an api test
    def test_create_film_list_collection_drama_fromweb(self):
        data = ct_api.get_jsonp('collecties/drama/payload.js')
        films = list(ct_data.create_films_list(data))
        self.assertGreater(len(films), 10)
        for item in films:
            # check if a Listitem can be created
            Listitem.from_dict(MagicMock(), **item)


# noinspection PyMethodMayBeStatic
class GetCollections(TestCase):
    def test_get_preferred_collection_from_web(self):
        """Get the list of collections that the website presents on the page
        'huur films', which is only a small subset of all available collections

        """
        coll_list = ct_api.get_preferred_collections()
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
            Listitem.from_dict(MagicMock(), **film)


# noinspection PyMethodMayBeStatic
class Gen(TestCase):
    def test_get_continue_watching(self):
        resp = ct_api.get_watched_films()
        check_films_data_list(resp, allow_none_values=False)

    def test_get_finished_watching(self):
        resp = ct_api.get_watched_films('finished')
        check_films_data_list(resp, allow_none_values=False)

    def test_get_purchased(self):
        resp = ct_api.get_rented_films()
        check_films_data_list(resp, allow_none_values=False)

    def get_stream_info(self):
        resp = ct_api.get_stream_info()


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
        """Only 2 character uppercase country codes are accepted"""
        result = ct_api.search_films(country='NL')
        self.assertGreater(len(result), 0, "Country 'NL' returned an empty list")
        for film_uuid in result:
            is_uuid(film_uuid)
        result = ct_api.search_films(country='Nl')
        self.assertListEqual(result, [])
        result = ct_api.search_films(country='nl')
        self.assertListEqual(result, [])

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
