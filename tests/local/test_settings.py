
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import logging as py_logging

import unittest
from unittest.mock import MagicMock, patch

from resources.lib import settings
from resources.lib import addon_log


class TestSettings(unittest.TestCase):
    @patch('resources.lib.ctree.ct_account.Session.login')
    def test_login(self, p_login):
        settings.login(MagicMock())
        p_login.assert_called_once()

    @patch('resources.lib.ctree.ct_account.Session.log_out')
    def test_logout(self, p_logout):
        settings.logout(MagicMock())
        p_logout.assert_called_once()

    @patch("resources.lib.addon_log.set_log_handler")
    def test_change_logger(self, p_set_log):
        logger = addon_log.logger

        self.assertTrue(hasattr(settings.change_logger, 'route'))

        with patch("resources.lib.kodi_utils.ask_log_handler", return_value=(0, 'kodi log')):
            settings.change_logger(MagicMock())
            p_set_log.assert_called_with(addon_log.KodiLogHandler)

        with patch("resources.lib.kodi_utils.ask_log_handler", return_value=(1, 'file log')):
            settings.change_logger(MagicMock())
            p_set_log.assert_called_with(addon_log.CtFileHandler)

        with patch("resources.lib.kodi_utils.ask_log_handler", return_value=(2, 'no log')) as p_ask:
            with patch.object(logger, 'handlers', new=[addon_log.CtFileHandler()]):
                settings.change_logger(MagicMock())
                p_set_log.assert_called_with(addon_log.DummyHandler)
                p_ask.assert_called_with(1)

        # Test default values passed to ask_log_handler().
        # logger not properly initialised
        with patch("resources.lib.kodi_utils.ask_log_handler", return_value=(1, 'file log')) as p_ask:
            with patch.object(logger, 'handlers', new=[]):
                settings.change_logger(MagicMock())
                p_ask.assert_called_with(0)

        # Current handler is of an unknown type
        with patch("resources.lib.kodi_utils.ask_log_handler", return_value=(1, 'file log')):
            with patch.object(logger, 'handlers', new=[py_logging.Handler()]):
                settings.change_logger(MagicMock())
                p_ask.assert_called_with(0)

    @patch("xbmcaddon.Addon.setSettingInt")
    def test_genre_sort_method(self, p_xbmc_settings):
        with patch("xbmcgui.Dialog.contextmenu", side_effect=(0, 1, 2, 3, 4, 5, 6, 7, 8)):
            for _ in range(9):
                settings.genre_sort_method.test()
        self.assertEqual(p_xbmc_settings.call_count, 18)
        # Dialog canceled
        p_xbmc_settings.reset_mock()
        with patch("xbmcgui.Dialog.contextmenu", return_value=-1):
            settings.genre_sort_method.test()
        p_xbmc_settings.assert_not_called()