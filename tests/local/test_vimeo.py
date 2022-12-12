
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support.testutils import open_json

from unittest import TestCase
from unittest.mock import patch

from resources.lib import vimeo


setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class TestGetHeight(TestCase):
    def test_height_as_int(self):
        h = vimeo.get_height(1080)
        self.assertEqual(h, 1080, "Expected height of 1080, but got {}".format(h))
        self.assertIsInstance(h, int)

    def test_height_as_float(self):
        h = vimeo.get_height(1080.5)
        self.assertEqual(h, 1080, "Expected height of 1080, but got {}".format(h))
        self.assertIsInstance(h, int)

    def test_height_as_text_wxh(self):
        h = vimeo.get_height('1920x1080')
        self.assertEqual(h, 1080, "Expected height of 1080, but got {}".format(h))
        self.assertIsInstance(h, int)

    def test_height_omitted(self):
        h = vimeo.get_height(None)
        self.assertEqual(h, 9999, "Expected height of 9999, but got {}".format(h))
        self.assertIsInstance(h, int)

    @patch('resources.lib.vimeo.xbmcgui.getScreenHeight', return_value=2160)
    def test_height_from_screen(self, _):
        h = vimeo.get_height(None)
        self.assertEqual(h, 2160)
        self.assertIsInstance(h, int)


@patch('resources.lib.vimeo.get_json', return_value=open_json('vimeo_stream_config.json'))
class TestGetVideoStream(TestCase):
    def test_get_stream_1080p(self, _):
        s = vimeo.get_steam_url('https://some/video', 1080)
        self.assertTrue(len(s) > 10)

    def test_get_stream_540p(self, _):
        s = vimeo.get_steam_url('https://some/video', 540)
        self.assertTrue(len(s) > 10)

    def test_get_stream_max_resolution(self, _):
        s = vimeo.get_steam_url('https://some/video')
        self.assertTrue(len(s) > 10)

    def test_get_stream_with_trailing_slash(self, _):
        s = vimeo.get_steam_url('https://some/video/')
        self.assertTrue(len(s) > 10)
