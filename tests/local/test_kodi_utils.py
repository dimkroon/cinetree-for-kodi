
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2024 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import unittest
from unittest.mock import patch

from tests.support import fixtures
fixtures.global_setup()


from resources.lib import kodi_utils


class TestKodiUtils(unittest.TestCase):
    def test_playtime_monitor(self):
        ptm = kodi_utils.PlayTimeMonitor()
        t = ptm.playtime
        self.assertFalse(ptm.wait_until_playing(0.5))
        self.assertIsNone(ptm.wait_while_playing())
        self.assertIsNone(ptm.onAVStarted())

    def test_ask_credentials(self):
        resp = kodi_utils.ask_credentials('name', 'pw')
        self.assertIsInstance(resp, tuple)
        self.assertEqual(2, len(resp))
        with patch('codequick.utils.keyboard', side_effect=('new_user', 'new_password')):
            self.assertTupleEqual(('new_user', 'new_password'), kodi_utils.ask_credentials('name', 'pw'))

    def test_show_msg_not_logged_in(self):
        self.assertTrue(kodi_utils.show_msg_not_logged_in())
        with patch('xbmcgui.Dialog.yesno', return_value=False):
            self.assertFalse(kodi_utils.show_msg_not_logged_in())

    def test_show_login_result(self):
        self.assertIsNone(kodi_utils.show_login_result(True))
        self.assertIsNone(kodi_utils.show_login_result(True, 'some msg'))
        self.assertIsNone(kodi_utils.show_login_result(False))

    def test_ask_login_retry(self):
        self.assertTrue(kodi_utils.ask_login_retry('some_reason'))
        self.assertTrue(kodi_utils.ask_login_retry('Invalid username'))
        self.assertTrue(kodi_utils.ask_login_retry('Invalid password'))
        with patch('xbmcgui.Dialog.yesno', return_value=False):
            self.assertFalse(kodi_utils.ask_login_retry('Invalid password'))

    @patch('xbmcgui.Dialog.textviewer')
    def test_show_low_credits_msg(self, p_viewer):
        with patch('xbmcgui.Dialog.yesno', return_value=False):
            self.assertIsNone(kodi_utils.show_low_credit_msg(0.0, 3.25))
            p_viewer.asser_not_called()
        with patch('xbmcgui.Dialog.yesno', return_value=True):
            self.assertIsNone(kodi_utils.show_low_credit_msg(0, 3.25))
            p_viewer.asser_called_once()

    def test_ask_log_handler(self):
        with patch('xbmcgui.Dialog.contextmenu', return_value=1):
            # return user selection
            result, name = kodi_utils.ask_log_handler(2)
            self.assertEqual(1, result)
            self.assertIsInstance(name, str)
        with patch('xbmcgui.Dialog.contextmenu', return_value=-1):
            # return default value when the user cancels the dialog
            result, _ = kodi_utils.ask_log_handler(2)
            self.assertEqual(2, result)
        with patch('xbmcgui.Dialog.contextmenu', return_value=-1):
            # default value cannot be mapped to a name
            result, name = kodi_utils.ask_log_handler(5)
            self.assertEqual(5, result)
            self.assertEqual('', name)

    @patch('xbmcgui.Dialog.textviewer')
    def test_confirm_rent_from_credit(self, p_dlg):
        with patch('xbmcgui.Dialog.yesno', return_value=True):
            result = kodi_utils.confirm_rent_from_credit('some film', 2.49, 10.0)
            self.assertIs(result, True)
            p_dlg.assert_not_called()

        with patch('xbmcgui.Dialog.yesno', return_value=False):
            result = kodi_utils.confirm_rent_from_credit('some film', 2.49, 10.0)
            self.assertIs(result, False)
            p_dlg.assert_called_once()

    @patch('resources.lib.kodi_utils.executeJSONRPC')
    def test_sync_play_state(self, p_jsonrpc):
        from resources.lib.ctree.ct_data import FilmItem
        from resources.lib.main import play_film
        film = FilmItem({'uuid': 'film-uid-1',
                         'content': {'endDate': '2050-01-01 01:01', 'duration': '60'},
                         'playtime': 900})
        film.data['params']['title'] = 'some film'

        # A partially watched film
        kodi_utils.sync_play_state(play_film, film)
        call_arg = p_jsonrpc.call_args.args[0]
        self.assertTrue('"position": 900' in call_arg)  # resume point is being set
        self.assertFalse('playcount' in call_arg)       # play count is left untouched

        # A fully watched film
        film.playtime = 0
        kodi_utils.sync_play_state(play_film, film)
        call_arg = p_jsonrpc.call_args.args[0]
        self.assertTrue('"playcount": 1' in call_arg)   # play count is being set
        self.assertTrue('"position": 0' in call_arg)    # resume point is cleared
