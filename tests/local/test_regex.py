
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import unittest
import re

from tests.support.testutils import doc_path


class FindQuotedStrings(unittest.TestCase):
    """Regex to find all parts within double quotes, ignoring escaped quotes"""
    pattern = re.compile(r'\"(?:\\"|[^\"])*\"')

    def test_find_with_escaped_quotes(self):
        str = r'originalTrailer:{_uid:"8a266edb-b3e6-4a01-bc0a-cefb8d8804cb",plugin:u,selectelectedByQuote:"\"something inside escaped quotes.\"",titleImageWidth:x,trailerVimeoURL:"https:\u002F\u002Fvimeo.com\u002F704452337",geoAllowCountries'
        matches = self.pattern.findall(str)
        self.assertEqual(
            ['"8a266edb-b3e6-4a01-bc0a-cefb8d8804cb"', r'"\"something inside escaped quotes.\""', r'"https:\u002F\u002Fvimeo.com\u002F704452337"'],
            matches
        )

    def test_file_collecties_drama(self):
        with open(doc_path("collecties-drama-payload.js")) as f:
            doc = f.read()
        matches = self.pattern.findall(doc)
        self.assertGreater(len(matches), 100)
        # for match in matches:
        #         print(match)
