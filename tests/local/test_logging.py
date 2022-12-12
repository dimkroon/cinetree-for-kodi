
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import logging as py_logging

import unittest
from unittest.mock import MagicMock, patch

from resources.lib import logging


class TestSetLogHandler(unittest.TestCase):
    def test_set_handler(self):
        logging.set_log_handler(logging.CtFileHandler)
        self.assertEqual(1, len(logging.logger.handlers))
        self.assertIsInstance(logging.logger.handlers[0], logging.CtFileHandler)

        logging.set_log_handler(logging.KodiLogHandler)
        self.assertEqual(1, len(logging.logger.handlers))
        self.assertIsInstance(logging.logger.handlers[0], logging.KodiLogHandler)

        # keep handler if no change
        handler = logging.DummyHandler()
        logging.logger.handlers = [handler]
        logging.set_log_handler(logging.DummyHandler)
        self.assertIs(handler, logging.logger.handlers[0])
