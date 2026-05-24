
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2026 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import unittest

from resources.lib import addon_log


class TestSetLogHandler(unittest.TestCase):
    def test_set_handler(self):
        addon_log.set_log_handler(addon_log.CtFileHandler)
        self.assertEqual(1, len(addon_log.logger.handlers))
        self.assertIsInstance(addon_log.logger.handlers[0], addon_log.CtFileHandler)

        addon_log.set_log_handler(addon_log.KodiLogHandler)
        self.assertEqual(1, len(addon_log.logger.handlers))
        self.assertIsInstance(addon_log.logger.handlers[0], addon_log.KodiLogHandler)

        # keep handler if no change
        handler = addon_log.DummyHandler()
        addon_log.logger.handlers = [handler]
        addon_log.set_log_handler(addon_log.DummyHandler)
        self.assertIs(handler, addon_log.logger.handlers[0])
