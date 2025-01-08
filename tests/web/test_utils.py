
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import unittest

from resources.lib import utils
from resources.lib import fetch


setUpModule = fixtures.setup_web_test


class VttToSrt(unittest.TestCase):
    def test_convert_subtitles_from_web(self):
        """Test various subtitles obtained directly from the web.

        Woman at war has a BOM and Windows style new lines
        """
        subtitles_urls = {
            'woman at war': 'https://api2.cinetree.nl/streams/p5xDzu7_K-Kveq1rTmZr_2EQ13jtED1g3Z4N_yofMNI/1660250404586/610ab4e64246d5001c7caccb/subtitles/nl.vtt',
            'the peanut butter falcon': 'https://api2.cinetree.nl/streams/DT_NgguXss7W_YiC3adm0lVB0FE-pI_u_Smq37hpmGA/1660252027362/62c6a87bf713f2d02430293d/subtitles/nl.vtt'
        }
        for title, url in subtitles_urls.items():
            vtt_doc = fetch.get_document(url)
            self.assertGreater(len(vtt_doc), 100)
            srt_doc = utils.vtt_to_srt(vtt_doc)
            self.assertGreater(len(srt_doc), 100)

