
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.object_checks import has_keys, check_film_data
from tests.support.testutils import HttpResponse, open_json

import json
import unittest
from unittest.mock import patch
from requests import exceptions

from resources.lib import storyblok


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class GetUrl(unittest.TestCase):
    @patch('urlquick.Session.request')
    def test_get_url(self, mocked_get):
        storyblok.get_url("doc.js")
        mocked_get.assert_called_once()
        url = mocked_get.call_args[0][1]
        self.assertTrue(url.startswith('https://api.storyblok.com') and url.endswith('doc.js'))

    @patch('urlquick.Session.request')
    def test_get_url_with_params(self, mocked_get):
        """Test if the function adds its own parameters of the same type as the caller has passed."""
        mocked_get.reset_mock()
        storyblok.get_url("doc.js", params={'q': 1})
        params = mocked_get.call_args[1]['params']
        self.assertIsInstance(params, dict)
        has_keys(params, 'q', 'token', 'version')
        # invalid object as params
        self.assertRaises(ValueError, storyblok.get_url, "doc.js", params=['q', 1])

    @patch('urlquick.Session.request', return_value=HttpResponse(status_code=400))
    def test_get_url_runs_into_http_error(self, mocked_get):
        self.assertRaises(exceptions.HTTPError, storyblok.get_url, "doc.js")
        mocked_get.assert_called_once()

    @patch('urlquick.Session.request', return_value=HttpResponse(status_code=429))
    def test_get_url_with_too_many_requests(self, mocked_get):
        """When the server returns HTTP status 429 (Too manyrequests) a retry is
        attempted after a delay of 1 sec.
        """
        self.assertRaises(exceptions.HTTPError, storyblok.get_url, "doc.js")
        self.assertEqual(2, mocked_get.call_count)

    @patch('urlquick.Session.request')
    def test_add_header(self, mocked_get):
        """Check that a header passed to function is added to the default headers"""
        storyblok.get_url("doc.js", headers={'custom_type': 'custom_value'})
        has_keys(mocked_get.call_args[1]['headers'], 'Referer', 'Origin', 'Accept', 'custom_type')

    @patch('urlquick.Session.request')
    def test_replace_header(self, mocked_get):
        """Check that a header passed to the function replaces the default header"""
        storyblok.get_url("doc.js", headers={'Accept': 'custom_value'})
        has_keys(mocked_get.call_args[1]['headers'], 'Referer', 'Origin', 'Accept')
        self.assertEqual('custom_value', mocked_get.call_args[1]['headers']['Accept'])


class GetUrlPage(unittest.TestCase):
    @patch('urlquick.Session.request',
           return_value=HttpResponse(headers={'total': 50}, content=json.dumps({'stories': ['a'] * 50}).encode()))
    def test_get_url_single_paging(self, mocked_get):
        resp, total = storyblok._get_url_page("mypage")
        self.assertListEqual(['a'] * 50, resp)
        self.assertEqual(50, total)
        mocked_get.assert_called_once()

    @patch('urlquick.Session.request',
           side_effect=[
                HttpResponse(headers={'total': 150}, content=json.dumps({'stories': ['a'] * 100}).encode()),
                HttpResponse(headers={'total': 150}, content=json.dumps({'stories': ['a'] * 50}).encode())])
    def test_get_url_multiple_page_in_one_go(self, mocked_get):
        resp, total = storyblok._get_url_page("page")
        self.assertListEqual(['a'] * 150, resp)
        self.assertEqual(150, total)
        self.assertEqual(2, mocked_get.call_count)

    @patch('urlquick.Session.request',
           side_effect=[
                HttpResponse(headers={'total': 150}, content=json.dumps({'stories': ['a'] * 100}).encode()),
                HttpResponse(headers={'total': 150}, content=json.dumps({'stories': ['a'] * 50}).encode())])
    def test_get_url_multiple_page_per_page(self, mocked_get):
        resp, total = storyblok._get_url_page("page", page=1)
        self.assertListEqual(['a'] * 100, resp)
        self.assertEqual(150, total)
        self.assertEqual(1, mocked_get.call_count)

    def test_invalid_arguments(self):
        self.assertRaises(ValueError, storyblok._get_url_page, "page", page=0)
        self.assertRaises(ValueError, storyblok._get_url_page, "page", items_per_page=0)
        self.assertRaises(ValueError, storyblok._get_url_page, "page", items_per_page=101)


class StoryByName(unittest.TestCase):
    @patch('resources.lib.storyblok.get_url', return_value=(open_json('st_blok/films-druk.json'), None))
    def test_story_by_name(self, _):
        data = storyblok.story_by_name('sldkjfv')
        self.assertEqual('Druk', data['name'])


@unittest.skip
class TestStoryContent(unittest.TestCase):
    """Some tests on film data that don't need to be run in automated tests"""
    def test_all_stored_films(self):
        films = open_json('st_blok/films.json')
        for film in films.values():
            check_film_data(film, ('tvodPrice', ))

    def test_find_gratis_films(self):
        films = open_json('st_blok/films.json')
        for film in films.values():
            price = film['content']['tvodPrice']
            if price == '' or int(price) == 0:
                print("Price of '{}' is '{}'".format(film['content']['title'], price))

    def test_find_films_with_end_date(self):
        films = open_json('st_blok/films.json')
        for film in films.values():
            end_date = film['content'].get('endDate')
            if end_date:
                print("Film {} has end date {}".format(film['content']['title'], end_date))

    def test_films_without_shops(self):
        films = open_json('st_blok/films.json')
        for film in films.values():
            shops = film['content'].get('shops')
            if not shops:
                print("Film {} has no shops: '{}'".format(film['content']['title'], shops))