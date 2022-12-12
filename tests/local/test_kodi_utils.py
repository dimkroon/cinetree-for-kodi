
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
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
    def test_show_rental_msg(self, p_viewer):
        with patch('xbmcgui.Dialog.yesno', return_value=False):
            self.assertIsNone(kodi_utils.show_rental_msg())
            p_viewer.asser_not_called()
        with patch('xbmcgui.Dialog.yesno', return_value=True):
            self.assertIsNone(kodi_utils.show_rental_msg())
            p_viewer.asser_called_once()

    @patch('xbmcgui.Dialog.contextmenu')
    def test_ask_resume_film(self, _):
        kodi_utils.ask_resume_film(10.1235)
        kodi_utils.ask_resume_film(300.1235)
        kodi_utils.ask_resume_film(3732.1235)

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
