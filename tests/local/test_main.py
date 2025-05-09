
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.testutils import open_jsonp, open_json, get_sb_film

import unittest
from unittest.mock import MagicMock, patch

import xbmcgui

from codequick import Listitem

from resources.lib import main
from resources.lib import errors
from resources.lib.ctree import ct_api
from resources.lib.ctree.ct_data import FilmItem

def setUpModule():
    fixtures.setup_local_tests()
    # Prevent webrequests to /favorites each time a film list is created.
    ct_api.favourites = []


tearDownModule = fixtures.tear_down_local_tests


@patch('resources.lib.storyblok.stories_by_uuids', new=get_sb_film)
class MainTest(unittest.TestCase):
    @patch('resources.lib.main.sync_watched_state')
    def test_root(self, p_sync):
        items = main.root.test()
        self.assertEqual(8, len(items))
        for item in items:
            self.assertIsInstance(item, Listitem)
        p_sync.assert_called_once()

    @patch('resources.lib.fetch.fetch_authenticated', return_value=open_json('watch-history.json'))
    @patch('xbmcaddon.Addon.getLocalizedString', lambda s, x: 'my list')
    def test_mijn_films(self, _):
        items = main.list_my_films.test()
        self.assertEqual(len(items), 4)
        for item in items:
            self.assertIsInstance(item, Listitem)

        items = main.list_my_films.test('finished')
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertIsInstance(item, Listitem)
            self.assertEqual(1, len(item.context))

        items = main.list_my_films.test('continue')
        self.assertEqual(len(items), 3)
        for item in items:
            self.assertIsInstance(item, Listitem)
            self.assertEqual(1, len(item.context))

        with patch('resources.lib.fetch.fetch_authenticated',
                   return_value=["3d3e2bb8-31ff-444f-909e-2a16a0fc4375", "070f9abd-9df9-47d1-bfbc-e83fdfea2e43"]):
            items = main.list_my_films.test('purchased')
            self.assertEqual(len(items), 2)
            for item in items:
                self.assertIsInstance(item, Listitem)
                self.assertEqual(1, len(item.context))

    def test_list_films_and_docus_deze_maand(self):
        # all subscription films
        with patch('resources.lib.fetch.get_json', return_value=open_json('films-svod.json')):
            items = main.list_films_and_docus.test(category='subscription')
            self.assertAlmostEqual(19, len(items), delta=3)
            for item in items:
                self.assertIsInstance(item, Listitem)

        # Hero items
        with patch('resources.lib.storyblok.get_url',
                   new=lambda *args, **kwargs: (open_json('st_blok/films-en-documentaires.json'), None)):
            items = main.list_films_and_docus.test(category='recommended')
            self.assertAlmostEqual(3, len(items), delta=1)
            for item in items:
                self.assertIsInstance(item, Listitem)

    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('films-payload.js'))
    def test_list_rental_collections(self, _):
        items = main.list_rental_collections.test()
        self.assertEqual(9, len(items))
        for item in items:
            self.assertIsInstance(item, Listitem)

    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('collecties-payload.js'))
    def test_list_all_collections(self, _):
        items = main.list_all_collections.test()
        self.assertGreater(len(items), 10)
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_list_genres(self):
        items = main.list_genres.test()
        self.assertEqual(len(ct_api.GENRES), len(items))
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_do_search(self):
        # no search_query
        self.assertFalse(main.do_search.test(''))

        # test search return a few items
        with patch('resources.lib.ctree.ct_api.search_films', return_value=["18ae971a-1ba5-4e2c-987f-5ba06c42fca8", "93d595ed-fcaf-4250-8ee3-87b006b92b87"]) as p_search:
            items = main.do_search.test('some_term')
            self.assertEqual(2, len(items))

        # Test returned list is limited to a max of 100 items
        all_uuids = list(open_json('st_blok/films.json').keys())
        with patch('resources.lib.ctree.ct_api.search_films', return_value=all_uuids):
            items = main.do_search(MagicMock(), 'some_term')
            self.assertLessEqual(len(items), 100)       # some items could (will) be filtered out on endDate

    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('originals_payload.js'))
    def test_list_originals(self, _):
        items = main.list_originals.test()
        self.assertGreater(len(items), 10)
        for item in items:
            self.assertIsInstance(item, Listitem)

    def test_list_shorts(self):
        # Submenu
        with patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('kort_payload.js')):
            items = main.list_shorts.test()
            self.assertEqual(len(items), 5)
            for item in items:
                self.assertIsInstance(item, Listitem)
        # All short films
        with patch('resources.lib.storyblok._get_url_page',
                   return_value=(open_json('st_blok/shorts.json').values(), 73)):
            items = main.list_shorts.test(list_films=True)
            self.assertEqual(len(items), 53)
            for item in items:
                self.assertIsInstance(item, Listitem)

    @patch('resources.lib.ctree.ct_api.get_jsonp', return_value=open_jsonp('collecties-prijswinnaars-payload.js'))
    def test_list_films_by_collection(self, _):
        items = list(main.list_films_by_collection(MagicMock(), ''))
        self.assertGreater(len(items), 10)
        for item in items:
            self.assertIsInstance(item, Listitem)

    @patch('resources.lib.storyblok.search', return_value=get_sb_film(genre='drama', page=1, items_per_page=50))
    def test_list_film_by_genre(self, _):
        items = list(main.list_films_by_genre(MagicMock(), genre='drama'))
        self.assertLessEqual(len(items), 51)

    @patch('resources.lib.fetch.web_request')
    def test_remove_from_list(self, p_web_request):
        uuid = 'my-film-uuid'
        main.remove_from_list.test(uuid, 'some title')
        call_kwargs = p_web_request.call_args.kwargs
        self.assertTrue(call_kwargs['url'].endswith(uuid))
        self.assertEqual(call_kwargs['method'].lower(), 'delete')
        # Canceled by user:
        p_web_request.reset_mock()
        with patch('xbmcgui.Dialog.yesno', return_value=False):
            main.remove_from_list.test(uuid, 'some title')
            p_web_request.assert_not_called()

    @patch('resources.lib.ctree.ct_api.set_resume_time')
    def test_monitor_progress(self, p_set_resume_time):
        # Test start and end time are reported
        with patch('resources.lib.kodi_utils.PlayTimeMonitor', return_value=MagicMock(return_value=True)):
            main.monitor_progress('123456sdf')
            self.assertEqual(2, p_set_resume_time.call_count)

        # Nothing reported when wait for start times out
        p_set_resume_time.reset_mock()
        with patch('resources.lib.kodi_utils.PlayTimeMonitor.wait_until_playing', return_value=False):
            p_set_resume_time.assert_not_called()
            main.monitor_progress('123456sdf')
            p_set_resume_time.assert_not_called()

    def test_play_ct_video(self):
        stream_inf = {'url': 'https://my.stream', 'subtitles': {'nl': 'my.subtitles'}}
        # test subtitles and steam info present
        with patch('resources.lib.ctree.ct_api.get_subtitles', return_value='my_subtitle.srt'):
            playitem = main.play_ct_video(stream_inf)
            self.assertIsInstance(playitem, xbmcgui.ListItem)
            self.assertListEqual(['my_subtitle.srt'], playitem._subtitles)
            self.assertEqual('https://my.stream', playitem._path)

        # test multiple subtitles
        stream_inf_2_subs = {'url': 'https://my.stream', 'subtitles': {'nl': 'nl.subtitles', 'en': 'en.subtitles'}}
        with patch('resources.lib.ctree.ct_api.get_subtitles', return_value='my_subtitle.srt'):
            playitem = main.play_ct_video(stream_inf_2_subs)
            self.assertListEqual(['my_subtitle.srt', 'my_subtitle.srt'], playitem._subtitles)

        # test ignore subtitles when fetch encounters HTTP Error
        with patch('resources.lib.ctree.ct_api.get_subtitles', side_effect=errors.FetchError):
            playitem = main.play_ct_video(stream_inf)
            self.assertIsInstance(playitem, xbmcgui.ListItem)
            self.assertFalse(hasattr(playitem, '_subtitles'))

        # play item without any subtitle information
        playitem = main.play_ct_video({'url': 'https://my.stream'})
        self.assertIsInstance(playitem, xbmcgui.ListItem)
        self.assertFalse(hasattr(playitem, '_subtitles'))
        self.assertEqual('https://my.stream', playitem._path)

        # test HLS protocol not supported fails silently
        with patch("inputstreamhelper.Helper.check_inputstream", return_value=False):
            with patch('resources.lib.ctree.ct_api.get_subtitles', return_value='my_subtitle.srt'):
                self.assertIs(main.play_ct_video(stream_inf), False)

    def test_play_trailer(self):
        # trailer form YouTube
        plugin = MagicMock()
        main.play_trailer(plugin, "https://www.youtube.com/myfilm")
        plugin.extract_source.assert_called_once_with('https://www.youtube.com/myfilm')

        # trailer from vimeo
        with patch('resources.lib.vimeo.get_json', return_value=open_json('vimeo_stream_config.json')):
            item = main.play_trailer(plugin, "https://www.vimeo.com/myfilm")
            self.assertTrue(item.startswith("https://"))
            self.assertTrue(item.endswith('.mp4'))

        # trailer from cinetree
        with patch('resources.lib.ctree.ct_api.get_stream_info', return_value=open_json('stream_info.json')):
            with patch("resources.lib.main.play_ct_video") as mocked_play:
                main.play_trailer(plugin, "https://api.cinetree.nl/bla/bla")
                mocked_play.assert_called_once()
                # check args are stream info dict and title
                self.assertIsInstance(mocked_play.call_args[0][0], dict)
                self.assertIsInstance(mocked_play.call_args[0][1], str)

        # trailer from something else
        item = main.play_trailer(plugin, "https://cloud.com/bla/bla")
        self.assertFalse(item)


@patch('resources.lib.storyblok.stories_by_uuids', get_sb_film)
class WatchList(unittest.TestCase):
    favourites = {
        'f621c2d2-4206-4824-a2d6-6e41427db6c1': '2024-11-11T20:19:18.007Z',
        '0577ba31-ff91-45a5-aa0a-4a81baaa4b6a': '2025-02-02T21:22:23.004Z'
    }

    def test_list_watch_list(self):
        with patch("resources.lib.ctree.ct_api.get_favourites", return_value=self.favourites):
            items = main.list_watchlist.test()
            self.assertEqual(2, len(items))
            for item in items:
                self.assertIsInstance(item, Listitem)
                self.assertEqual(1, len(item.context))

    def test_add_remove(self):
        with patch("resources.lib.ctree.ct_api.edit_favourites") as p_edit, \
             patch('xbmc.executebuiltin') as p_exec:
            main.edit_watchlist.test('my-uui-id', 'add')
        p_edit.assert_called_once_with('my-uui-id', 'add')
        p_exec.assert_called_once()

        with patch("resources.lib.ctree.ct_api.edit_favourites") as p_edit:
            main.edit_watchlist.test('my-uui-id', 'remove')
        p_edit.assert_called_once_with('my-uui-id', 'remove')


@patch("resources.lib.ctree.ct_api.get_subtitles", return_value=None)
class PlayFilm(unittest.TestCase):
    @patch('resources.lib.main.pay_from_ct_credit', return_value=False)
    def test_play_film_from_uuid(self, p_pay_from_credit, _):
        with patch('resources.lib.ctree.ct_api.get_stream_info', return_value=open_json('stream_info.json')):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertIsInstance(playitem, xbmcgui.ListItem)
            p_pay_from_credit.assert_not_called()
        with patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=errors.NotPaidError):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertFalse(playitem)
            p_pay_from_credit.assert_called_once()
        p_pay_from_credit.reset_mock()
        with patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=errors.NoSubscriptionError):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertFalse(playitem)
            p_pay_from_credit.assert_not_called()
        with patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=errors.HttpError(404, '')):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertFalse(playitem)
            p_pay_from_credit.assert_not_called()
        with patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=errors.FetchError):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertFalse(playitem)
            p_pay_from_credit.assert_not_called()
        with patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=ValueError):
            playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
            self.assertIsInstance(playitem, type(False))
            p_pay_from_credit.assert_not_called()

    @patch('resources.lib.ctree.ct_api.get_stream_info', side_effect=(errors.NotPaidError,
                                                                      open_json('stream_info.json')))
    @patch('resources.lib.main.pay_from_ct_credit', return_value=True)
    def test_play_film_after_paying(self, p_pay_from_credit, p_get_stream_info, _):
        playitem = main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
        self.assertIsInstance(playitem, xbmcgui.ListItem)
        p_pay_from_credit.assert_called_once()
        self.assertEqual(2, p_get_stream_info.call_count)

    def test_play_film_resume_time(self, _):
        strm_info = open_json('stream_info.json')
        strm_info['playtime'] = 1560.236
        with patch('resources.lib.ctree.ct_api.get_stream_info', return_value=strm_info):
            main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
        strm_info['playtime'] = 0
        with patch('resources.lib.ctree.ct_api.get_stream_info', return_value=strm_info):
            main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)
        del strm_info['playtime']
        with patch('resources.lib.ctree.ct_api.get_stream_info', return_value=strm_info):
            main.play_film.test('', 'ec0407a8-24a1-47a1-8bbf-61ada5f6610f', None)


@patch('resources.lib.kodi_utils.show_low_credit_msg')
@patch('resources.lib.ctree.ct_api.get_payment_info', return_value=(4.3, '1982873hfmalk'))
class PayFromCredit(unittest.TestCase):
    @patch('resources.lib.ctree.ct_api.pay_film', return_value=True)
    @patch('resources.lib.ctree.ct_api.get_ct_credits', return_value=10)
    def test_pay_successfully(self, _, p_pay_film, __, p_show_low_credit):
        with patch('resources.lib.kodi_utils.confirm_rent_from_credit', return_value=True):
            result = main.pay_from_ct_credit('my_film', 'my-film-uuid')
            self.assertIs(result, True)
            p_show_low_credit.assert_not_called()
            p_pay_film.assert_called_once()

    @patch('resources.lib.ctree.ct_api.pay_film', return_value=True)
    @patch('resources.lib.ctree.ct_api.get_ct_credits', return_value=10)
    def test_pay_canceled(self, _, p_pay_film, __, p_show_low_credit):
        with patch('resources.lib.kodi_utils.confirm_rent_from_credit', return_value=False):
            result = main.pay_from_ct_credit('my_film', 'my-film-uuid')
            self.assertIs(result, False)
            p_show_low_credit.assert_not_called()
            p_pay_film.assert_not_called()

    @patch('resources.lib.ctree.ct_api.pay_film', return_value=True)
    @patch('resources.lib.ctree.ct_api.get_ct_credits', return_value=2)
    def test_not_enough_credit(self, _, p_pay_film, __, p_show_low_credit):
        result = main.pay_from_ct_credit('my_film', 'my-film-uuid')
        self.assertIs(result, False)
        p_show_low_credit.assert_called_once()
        p_pay_film.assert_not_called()

    @patch('resources.lib.ctree.ct_api.pay_film', return_value=False)
    @patch('resources.lib.ctree.ct_api.get_ct_credits', return_value=10)
    def test_payment_failed(self, _, p_pay_film, __, p_show_low_credit):
        MSG_ID_PAYMENT_FAILED = 30625
        with patch('resources.lib.kodi_utils.ok_dialog') as p_ok_dlg:
            result = main.pay_from_ct_credit('my_film', 'my-film-uuid')
        self.assertIs(result, False)
        p_show_low_credit.assert_not_called()
        p_pay_film.assert_called_once()
        p_ok_dlg.assert_called_with(MSG_ID_PAYMENT_FAILED)


@patch('resources.lib.kodi_utils.executeJSONRPC')
class SyncWatchedState(unittest.TestCase):
    def test_sync_films(self, p_jsonrpc):
        watched = [FilmItem({'uuid': 'film-uid-1',
                             'content': {'endDate': '2050-01-01 01:01', 'duration': '60'},
                             'playtime': 900}),
                   FilmItem({'uuid': 'film-uid-2',
                             'content': {'endDate': '2050-01-01 01:01', 'duration': '90'},
                             'playtime': 1200})
                   ]
        with patch('resources.lib.ctree.ct_api.get_watched_films', return_value=watched), \
             patch('resources.lib.main.PersistentDict._load', return_value={}):
            main.sync_watched_state()
            self.assertEqual(p_jsonrpc.call_count, 2)
        # Now it has been synced it will not sync the same status again.
        p_jsonrpc.reset_mock()
        with patch('resources.lib.ctree.ct_api.get_watched_films', return_value=watched):
            main.sync_watched_state()
            p_jsonrpc.assert_not_called()
        # But changes will be synced.
        p_jsonrpc.reset_mock()
        watched[0].playtime = 0
        with patch('resources.lib.ctree.ct_api.get_watched_films', return_value=watched):
            main.sync_watched_state()
            p_jsonrpc.assert_called_once()
