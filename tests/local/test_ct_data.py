
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import datetime
import itertools
from urllib.parse import quote_plus
from copy import deepcopy

from unittest import TestCase
from unittest.mock import MagicMock, patch

from codequick import Listitem

from tests.support.testutils import open_jsonp, open_json
from tests.support.object_checks import check_collection, has_keys

from resources.lib.ctree import ct_data


def film_item(content, show_price=True):
    film_item = ct_data.FilmItem({'content': content}, show_price)
    return film_item


# noinspection PyMethodMayBeStatic
class CreateFilmItem(TestCase):
    def test_create_invalid_item(self):
        self.assertFalse(ct_data.FilmItem(None))
        self.assertFalse(ct_data.FilmItem(''))
        self.assertFalse(ct_data.FilmItem({}))
        self.assertFalse(ct_data.FilmItem({'a': 1}))

        self.assertIsNone(ct_data.FilmItem(None).data)
        self.assertIsNone(ct_data.FilmItem('').data)
        self.assertIsNone(ct_data.FilmItem({}).data)
        self.assertIsNone(ct_data.FilmItem({'a': 1}).data)

    def test_create_film_item(self):
        item_data = film_item({}).data
        has_keys(item_data, 'label', 'art', 'info', 'params')
        has_keys(item_data['params'], 'title', 'slug')

    def test_end_date(self):
        # date in the future
        item_data = film_item({'endDate': '2060-01-01 00:00'}).data
        self.assertIsInstance(item_data, dict)
        # date in the past
        self.assertIsNone(film_item({'endDate': '2021-04-22 00:00'}).data)
        # date in other format is rejected
        self.assertIsNone(film_item({'endDate': '2060-04-22'}).data)
        self.assertIsNone(film_item({'endDate': '22-04-2022 00:00'}).data)

    @patch("resources.lib.ctree.ct_data.TXT_SUBCRIPTION_FILM", 'is a subscription film')
    def test_show_subscription_availability(self):
        """If subscription films reach the end date a notification is added to the title"""
        now = datetime.datetime.now(datetime.timezone.utc)
        item_data = film_item({'svodEndDate': '2060-01-01 00:00', 'title': ''}).data
        self.assertEqual('is a subscription film', item_data['info']['plot'])

        end_date = now + datetime.timedelta(hours=4)
        item_data = film_item({'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}).data
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        end_date = now + datetime.timedelta(days=1)
        item_data = film_item({'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}).data
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        end_date = now + datetime.timedelta(days=10)
        item_data = film_item({'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}).data
        self.assertTrue("[COLOR orange][/COLOR]" in item_data['info']['title'])   # localized strings return '' in tests

        # No message added when film is still more than 10 days available
        end_date = now + datetime.timedelta(days=11)
        item_data = film_item({'svodEndDate': end_date.strftime("%Y-%m-%d %H:%M"), 'title': ''}).data
        self.assertTrue("" in item_data['info']['title'])   # localized strings return '' in tests

    @patch("resources.lib.ctree.ct_data.TXT_SUBCRIPTION_FILM", 'is a subscription film')
    def test_show_price(self):
        """Price should only be added to plot if the film is currently not within the subscription plan.
        """
        item_data = film_item({'tvodPrice': '499'}).data
        self.assertEqual('[B]€ 4,99[/B]', item_data['info']['plot'])

        # The film is in the monthly subscription (i.e. svodEndDate is in the future)
        item_data = film_item({'tvodPrice': '499', 'svodEndDate': '2060-01-01 00:00',
                               'title': '', 'shortSynopsis': "About the film"}).data
        self.assertTrue(item_data['info']['plot'].endswith('is a subscription film'))

        item_data = film_item({'tvodPrice': '499', 'svodEndDate': '2060-01-01 00:00', 'title': ''},
                              show_price=False).data
        self.assertFalse(item_data['info']['plot'].endswith('is a subscription film'))


class GetFilmsList(TestCase):
    def test_create_film_list_storyblok(self):
        sb_films = itertools.islice(open_json('st_blok/films.json').values(), 4)
        films = ct_data.create_films_list(sb_films, 'storyblok')
        self.assertEqual(len(films), 4)

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


@patch('resources.lib.ctree.ct_data.TXT_FOR_MEMBERS', 'for members')
class TestPriceInfo(TestCase):
    def test_full_price_info(self):
        fi = film_item({'tvodPrice': 450, 'tvodSubscribersPrice': 350})
        self.assertEqual('[B]€ 4,50[/B]\n[B]€ 3,50[/B] for members', fi.price_info)

    def test_free_film(self):
        fi = film_item({'tvodPrice': 0})
        self.assertEqual('[B]€ 0,00[/B]', fi.price_info)

    def test_missing_prince_info(self):
        fi = film_item({})
        self.assertEqual('', fi.price_info)


@patch('xbmcaddon.Addon.getLocalizedString',
       lambda self, x: {
            30514: 'over a year',
            30515: 'for {} months',
            30516: 'for {} weeks',
            30317: 'for {} days',
            30318: 'for {} hours'
            }.get(x))
class TestAvailability(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.now = datetime.datetime.now(datetime.timezone.utc)

    def future(self, months=0, weeks=0, days=0, hours=0, minutes=0):
        days = days + weeks * 7 + months * 30
        # Add an extra minutes because FilmItem.availability calculates 'now' just a little later than this class
        d_dif = datetime.timedelta(days=days, hours=hours, minutes=minutes + 1)
        return (self.now + d_dif).strftime('%Y-%m-%d %H:%M')

    def test_availability_year(self):
        fi = film_item({'endDate': self.future(days=366)})
        self.assertEqual('over a year', fi.availability)

    def test_availability_months(self):
        fi = film_item({'endDate': self.future(days=365)})
        self.assertEqual('for 12 months', fi.availability)
        fi = film_item({'endDate': self.future(days=61)})
        self.assertEqual('for 2 months', fi.availability)

    def test_availability_weeks(self):
        fi = film_item({'endDate': self.future(days=60)})
        self.assertEqual('for 8 weeks', fi.availability)
        fi = film_item({'endDate': self.future(days=15)})
        self.assertEqual('for 2 weeks', fi.availability)

    def test_availability_days(self):
        fi = film_item({'endDate': self.future(days=14)})
        self.assertEqual('[COLOR orange]for 14 days[/COLOR]', fi.availability)
        fi = film_item({'endDate': self.future(days=2)})
        self.assertEqual('[COLOR orange]for 2 days[/COLOR]', fi.availability)

    def test_availability_hours(self):
        fi = film_item({'endDate': self.future(hours=48)})
        self.assertEqual('[COLOR orange]for 2 days[/COLOR]', fi.availability)
        fi = film_item({'endDate': self.future(hours=47)})
        self.assertEqual('[COLOR orange]for 47 hours[/COLOR]', fi.availability)
        fi = film_item({'endDate': self.future(hours=1)})
        self.assertEqual('[COLOR orange]for 1 hours[/COLOR]', fi.availability)
        fi = film_item({'endDate': self.future(minutes=30)})
        self.assertEqual('[COLOR orange]for 0 hours[/COLOR]', fi.availability)


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
        self.FilmItem = ct_data.FilmItem(None)
        self.FilmItem.content = self.film_data

    def test_prefer_vimeo_all_present(self):
        trailer = self.FilmItem._select_trailer_url(False)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_vimeo_but_vimeo_not_present(self):
        self.FilmItem.content.pop('trailerVimeoURL')
        trailer = self.FilmItem._select_trailer_url(False)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_vimeo_but_vimeo_is_empty_string(self):
        self.FilmItem.content['trailerVimeoURL'] = ''
        trailer = self.FilmItem._select_trailer_url(False)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_vimeo_but_vimeo_is_empty_string_and_originalTrailer_not_present(self):
        fi = film_item({'trailerVimeoURL': '', 'originalTrailerURL': self.orig_url})
        trailer = fi._select_trailer_url(False)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_vimeo_but_vimeo_is_absent_and_originalTrailer_selected_is_None(self):
        fi = film_item({'originalTrailer': {'selected': None, "plugin": "cinetree-autocomplete"},
                        'originalTrailerURL': self.orig_url})
        trailer = fi._select_trailer_url(False)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_vimeo_but_vimeo_is_absent_and_originalTrailer_plugin_is_wrong_type(self):
        fi = film_item({'originalTrailer': {'selected': '1234abcd', "plugin": "autocomplete"},
                        'originalTrailerURL': self.orig_url})
        trailer = fi._select_trailer_url(False)
        self.assertEqual('', trailer)

    def test_prefer_original_all_present(self):
        trailer = self.FilmItem._select_trailer_url(True)
        self.assertEqual(self.expect_cinetree, trailer)

    def test_prefer_original_but_originalTrailer_not_present(self):
        self.FilmItem.content.pop('originalTrailer')
        trailer = self.FilmItem._select_trailer_url(True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_absent_and_originalUrl_empty(self):
        fi = film_item({'trailerVimeoURL': self.vimeo_url, 'originalTrailerURL': ''})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_original_but_both_originalTrailer_and_originalUrl_absent(self):
        fi = film_item({'trailerVimeoURL': self.vimeo_url})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_whitspace_in_url(self):
        fi = film_item({'trailerVimeoURL': ' ' + self.vimeo_url})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_vimeo, trailer)

        fi = film_item({'trailerVimeoURL': self.vimeo_url + ' '})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_vimeo, trailer)

        fi = film_item({'originalTrailerURL': ' ' + self.orig_url + ' '})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_selected_is_None(self):
        # noinspection PyTypedDict
        self.FilmItem.content['originalTrailer']['selected'] = None
        trailer = self.FilmItem._select_trailer_url( True)
        self.assertEqual(self.expect_youtube, trailer)

    def test_prefer_original_but_originalTrailer_selected_is_None_and_originalUrl_is_empty(self):
        fi = film_item({'originalTrailer': {'selected': None, "plugin": "cinetree-autocomplete"},
                        'trailerVimeoURL': self.vimeo_url, 'originalTrailerURL': ''})
        trailer = fi._select_trailer_url(True)
        self.assertEqual(self.expect_vimeo, trailer)

    def test_prefer_original_but_originalTrailer_plugin_is_wrong_type(self):
        self.FilmItem.content['originalTrailer']['plugin'] = "autocomplete"
        trailer = self.FilmItem._select_trailer_url(True)
        self.assertEqual('', trailer)

    def test_no_trailers_present(self):
        fi = film_item({})
        self.assertEqual('', fi._select_trailer_url(True))
        self.assertEqual('', fi._select_trailer_url(False))

    def test_all_trailers_are_empty_strings(self):
        fi = film_item({'trailerVimeoURL': '', 'originalTrailerURL': ''})
        self.assertEqual('', fi._select_trailer_url(True))
        self.assertEqual('', fi._select_trailer_url(False))

    def test_invalid_trailer_data(self):
        """The function should fail silently and just return an empty string
        """
        # First ensure the original trailer is returned on valid data
        self.assertEqual(self.expect_cinetree, self.FilmItem._select_trailer_url(True))

        del self.FilmItem.content['originalTrailer']['plugin']
        self.assertEqual('', self.FilmItem._select_trailer_url(True))
        # noinspection PyTypedDict
        self.FilmItem.content['originalTrailer'] = "https://some.trailer.com"
        self.assertEqual('', self.FilmItem._select_trailer_url(True))


class ParseEndDate(TestCase):
    def test_not_expired_date(self):
        dt, expired = ct_data.parse_end_date('3024-11-12 18:42')
        self.assertIsInstance(dt, datetime.datetime)
        self.assertEqual(3024, dt.year)
        self.assertEqual(11, dt.month)
        self.assertEqual(12, dt.day)
        self.assertEqual(18, dt.hour)
        self.assertEqual(42, dt.minute)
        self.assertEqual(0, dt.second)
        self.assertIs(expired, False)

    def test_expired_date(self):
        dt, expired = ct_data.parse_end_date('2024-11-12 18:42')
        self.assertIsInstance(dt, datetime.datetime)
        self.assertIs(expired, True)


class Generic(TestCase):
    def test_list_from_items_string(self):
        # noinspection PyTypeChecker
        self.assertEqual(None, ct_data.list_from_items_string(None))
        self.assertEqual(None, ct_data.list_from_items_string(''))
        self.assertEqual(["bla"], ct_data.list_from_items_string('bla'))
        self.assertEqual(['bli', ' bla', ' blob'], ct_data.list_from_items_string('bli, bla, blob'))

    def test_parse_end_date(self):
        tz_utc = datetime.timezone.utc
        # expired
        self.assertEqual((datetime.datetime(year=2020, month=1, day=2, hour=10, minute=22, tzinfo=tz_utc), True),
                         ct_data.parse_end_date("2020-01-02 10:22"))
        # not expired
        self.assertEqual((datetime.datetime(year=3020, month=1, day=2, hour=10, minute=22, tzinfo=tz_utc), False),
                         ct_data.parse_end_date("3020-01-02 10:22"))
        # Invalid
        self.assertEqual((None, False), ct_data.parse_end_date(None))
        self.assertEqual((None, False), ct_data.parse_end_date(''))
        self.assertEqual((None, True), ct_data.parse_end_date('1-12-42'))