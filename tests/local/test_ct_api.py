# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import os.path

from unittest import TestCase
from unittest.mock import patch, PropertyMock

from tests.support.testutils import open_jsonp, open_doc, open_json, HttpResponse
from tests.support.object_checks import check_collection

from resources.lib.ctree import ct_api
from resources.lib import errors, utils
from resources.lib import fetch


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


@patch('resources.lib.ctree.ct_api.get_jsonp_url', lambda x, force_refresh=False: 'https://' + x)
class GetJsonp(TestCase):
    @patch("resources.lib.fetch.get_document", open_doc('films-payload.js'))
    def test_get_jsonp_doc(self):
        result = ct_api.get_jsonp("mypath")
        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    def test_get_jsop_web_not_found_error(self):
        """Http error 404 is returned if the timestamp in the url has expired, making the
        url invalid. The function is to update the url and try once again.
        """
        # Test second try succeeds
        with patch("resources.lib.fetch.get_document", side_effect=(errors.HttpError(404, ''), '{}')) as mocked_get:
            resp = ct_api.get_jsonp("mypath")
            self.assertEqual({}, resp)
            mocked_get.assert_called_with('https://mypath')
            self.assertEqual(2, mocked_get.call_count)

        # Test second try fails again.
        with patch("resources.lib.fetch.get_document", side_effect=errors.HttpError(404, '')) as mocked_get:
            self.assertRaises(errors.HttpError, ct_api.get_jsonp, "mypath")
            mocked_get.assert_called_with('https://mypath')
            self.assertEqual(2, mocked_get.call_count)

    @patch("resources.lib.fetch.get_document", side_effect=errors.HttpError(400, ''))
    def test_get_jsop_web_other_error(self, mocked_get):
        """Other error should be raised without retrying"""
        self.assertRaises(errors.HttpError, ct_api.get_jsonp, "mypath")
        mocked_get.assert_called_once_with('https://mypath')

    @patch("resources.lib.jsonp.parse")
    @patch("resources.lib.jsonp.parse_simple")
    def test_get_jsonp_parser_selection(self, mocked_simple_parse, mocked_parse):
        with patch("resources.lib.fetch.get_document", return_value='zdfgsdf __NUXT_=(function()'):
            ct_api.get_jsonp('mypath')
        with patch("resources.lib.fetch.get_document", return_value='pldfksdjgo8  '):
            ct_api.get_jsonp('mypath')
        mocked_parse.assert_called_once_with('zdfgsdf __NUXT_=(function()')
        mocked_simple_parse.assert_called_once_with('pldfksdjgo8  ')


@patch('resources.lib.ctree.ct_api.get_jsonp_url', lambda x, force_refresh=False: 'https://' + x)
class CreateStreamInfoUrl(TestCase):
    @patch("resources.lib.fetch.get_document", open_doc('films_el-sicatio_room_164-payload.js'))
    def test_create_stream_info_url_from_uuid(self):
        url = ct_api.create_stream_info_url('123-abc', 'films/films_el-sicatio_room_164')
        self.assertEqual('https://api.cinetree.nl/films/123-abc', url)
        url = ct_api.create_stream_info_url('123-abc')
        self.assertEqual('https://api.cinetree.nl/films/123-abc', url)

    @patch("resources.lib.storyblok.get_url", return_value=(open_json('st_blok/films-druk.json'), None))
    def test_create_stream_info_url_from_slug(self, _):
        url = ct_api.create_stream_info_url(None, 'films/druk')
        self.assertEqual('https://api.cinetree.nl/films/' + 'f0770c12-6cb4-4b7e-b977-8385aa3d71bf', url)

    @patch("resources.lib.storyblok.get_url", side_effect=errors.HttpError(404, 'Not Found'))
    def test_create_stream_info_url_from_slug_with_web_error(self, _):
        self.assertRaises(errors.FetchError, ct_api.create_stream_info_url, None, 'films/films_el-sicatio_room_164')

    @patch("resources.lib.storyblok.get_url", return_value=(open_doc('manifest.js'), None))
    def test_create_stream_info_url_from_slug_with_invalid_document(self, _):
        self.assertRaises(errors.FetchError, ct_api.create_stream_info_url, None, 'films/films_el-sicatio_room_164')


# noinspection PyMethodMayBeStatic
class Collections(TestCase):
    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('films-payload.js'))
    def test_get_preferred_collections(self, _):
        col_list = list(ct_api.get_preferred_collections())
        self.assertGreater(len(col_list), 1)
        for col in col_list:
            check_collection(self, col)

    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('collecties-payload.js'))
    def test_get_all_collections(self, _):
        col_list = list(ct_api.get_collections())
        self.assertGreater(len(col_list), 1)
        for col in col_list:
            check_collection(self, col)


@patch('resources.lib.fetch.fetch_authenticated',
       return_value= [
           {'uuid': 'f621c2d2-4206-4824-a2d6-6e41427db6c1', 'createdAt': '2024-11-11T20:19:18.007Z'},
           {'uuid': '0577ba31-ff91-45a5-aa0a-4a81baaa4b6a', 'createdAt': '2025-02-02T21:22:23.004Z'}
    ])
class GetFavourites(TestCase):
    def test_get_favourites_new(self, p_fetch):
        ct_api.favourites = None
        favs = ct_api.get_favourites()
        self.assertDictEqual(favs,
                             {'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z',
                              '0577ba31-ff91-45a5-aa0a-4a81baaa4b6a': '2025-02-02T21:22:23.004Z'})
        self.assertEqual(favs, ct_api.favourites)
        p_fetch.assert_called_once()

    def test_get_favourites_existing(self, p_fetch):
        ct_api.favourites = {'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z'}
        favs = ct_api.get_favourites()
        self.assertDictEqual(favs, {'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z'})
        p_fetch.assert_not_called()

    def test_get_favourites_force_refresh(self, p_fetch):
        ct_api.favourites = {'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z'}
        favs = ct_api.get_favourites(refresh=True)
        self.assertDictEqual(favs,
                             {'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z',
                              '0577ba31-ff91-45a5-aa0a-4a81baaa4b6a': '2025-02-02T21:22:23.004Z'})
        p_fetch.assert_called_once()


class EditFavourites(TestCase):
    def setUp(self):
        ct_api.favourites = {'first-uuid': '2025-04-04T01:02:03.004Z'}

    def test_add_favourite(self):
        with patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(status_code=200)) as p_fetch:
            self.assertTrue(ct_api.edit_favourites('my-film-uuid', 'add'))
            self.assertTrue(p_fetch.call_args.kwargs['url'].endswith('my-film-uuid'))
            self.assertEqual(p_fetch.call_args.kwargs['method'], 'put')
            self.assertEqual(len(ct_api.favourites), 2)
            self.assertTrue('my-film-uuid' in ct_api.favourites)
        with patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(status_code=404)):
            self.assertFalse(ct_api.edit_favourites('other-film-uuid', 'add'))
            self.assertEqual(len(ct_api.favourites), 2)

    @patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(status_code=200))
    def test_remove_favourite(self, p_fetch):
        self.assertTrue(ct_api.edit_favourites('first-uuid', 'remove'))
        self.assertTrue(p_fetch.call_args.kwargs['url'].endswith('first-uuid'))
        self.assertEqual(p_fetch.call_args.kwargs['method'], 'delete')
        self.assertDictEqual(ct_api.favourites, {})

    def test_invalid_action(self):
        self.assertRaises(KeyError, ct_api.edit_favourites, 'my-uuid', action='delete')


class Gen(TestCase):
    @patch('resources.lib.utils.CacheMgr.version', PropertyMock(return_value='abcde'))
    @patch('resources.lib.fetch.get_document', open_doc('originals_payload.js'))
    def test_get_originals(self):
        data = ct_api.get_originals()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 10)

    def test_get_subtitles(self):
        # noinspection PyTypeChecker
        # Check return value when url to subtitles is not provided.
        srt_file = ct_api.get_subtitles(None, None)
        self.assertEqual(srt_file, '')
        srt_file = ct_api.get_subtitles('', '')
        self.assertEqual(srt_file, '')

        # check if the file is actually written
        try:
            os.remove(utils.get_subtitles_temp_file())
        except FileNotFoundError:
            pass
        with patch('resources.lib.fetch.get_document', open_doc('vtt/subtitles-woman_at_war.vtt')):
            self.assertFalse(os.path.isfile(srt_file))              # assert that initially file does not exist
            srt_file = ct_api.get_subtitles("https://my/subtitles", 'nl')
            self.assertTrue(os.path.isfile(srt_file))               # assert that file now exists and has content
            with open(srt_file, 'r') as f:
                self.assertGreater(len(f.read()), 100)

    def test_set_resume_time(self):
        """Test reporting playtime back to Cinetree."""
        wacthhistoryid = '13456'
        playtime = 128.123456789
        with patch('resources.lib.fetch.fetch_authenticated') as put_mock:
            ct_api.set_resume_time(wacthhistoryid, playtime)
            put_mock.assert_called_once()
            self.assertEqual(fetch.put_json, put_mock.call_args[0][0])                  # must use a PUT
            self.assertTrue(wacthhistoryid in put_mock.call_args[0][1])                 # wathchistoryid is part url
            self.assertEqual({'playtime': 128.123}, put_mock.call_args[1]['data'])      # playtime in data rounded to 3 decimals

        with patch('resources.lib.fetch.fetch_authenticated', side_effect=errors.FetchError):
            # Fails silently on errors
            ct_api.set_resume_time('13456', 128.123456789)

    @patch('resources.lib.fetch.fetch_authenticated', return_value=open_json('payment_info.json'))
    def test_get_payment_info(self, _):
        amount, transaction_id = ct_api.get_payment_info('some-film-uuid')
        self.assertIsInstance(amount, float)
        self.assertIsInstance(transaction_id, str)

    @patch('resources.lib.fetch.fetch_authenticated', return_value=open_json('me.json'))
    def test_get_credit_amount(self, _):
        cur_credits = ct_api.get_ct_credits()
        self.assertEqual(cur_credits, 6.51)

    def test_pay_film(self):
        with patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(content=b'')) as p_fetch:
            result = ct_api.pay_film('my-film-uuid', 'film-title', 'ddskfkj6593498u', 3.49)
            self.assertIs(result, True)
            self.assertTrue(p_fetch.call_args.kwargs.get('method') == 'post')
        with patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(content=b'some text')):
            result = ct_api.pay_film('my-film-uuid', 'film-title', 'ddskfkj6593498u', 3.49)
            self.assertIs(result, True)
        with patch('resources.lib.fetch.fetch_authenticated', return_value=HttpResponse(400, content=b'')):
            result = ct_api.pay_film('my-film-uuid', 'film-title', 'ddskfkj6593498u', 3.49)
            self.assertIs(result, False)
        with patch('resources.lib.fetch.fetch_authenticated', side_effect=errors.HttpError):
            result = ct_api.pay_film('my-film-uuid', 'film-title', 'ddskfkj6593498u', 3.49)
            self.assertIs(result, False)
