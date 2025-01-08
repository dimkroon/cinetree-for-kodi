# ------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------
from support.testutils import save_json
from tests.support import fixtures
fixtures.global_setup()


import json
import time
from unittest import TestCase

import requests

from support import testutils
from tests.support.object_checks import has_keys, expect_keys


class TestSearchEndPoint(TestCase):
    def setUp(self):
        self.now_ms = int(time.time() * 1000)

    def do_search(self, term):
        url = 'https://ap2sg0z16n-dsn.algolia.net/1/indexes/films/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.24.0)%3B%20Browser'
        url = 'https://ap2sg0z16n-dsn.algolia.net/1/indexes/films/query'
        headers = {
            'x-algolia-api-key': '0fd5e1415555be4cda53a8c870cb665e',
            'x-algolia-application-id': 'AP2SG0Z16N',
            'referer': 'https://cinetree.nl/'
        }
        form_data = {
            'query': term,
            'filters': f'(location:"films" OR location:"shorts") AND startDateMs<={self.now_ms} AND endDateMs>={self.now_ms} AND shops:cinetree.nl',
            'disableExactOnAttributes':['genre'],
            'hitsPerPage':50}
        resp = requests.post(url, data=json.dumps(form_data), headers=headers)
        return resp

    def test_search_results(self):
        resp = self.do_search('war')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('application/json; charset=UTF-8', resp.headers['content-type'])
        data = json.loads(resp.content)
        save_json(data, 'algolia/search.json')
        results = data['hits']
        for film_data in results:
            has_keys(film_data, 'title', 'objectID', 'full_slug', '_highlightResult')
            expect_keys(film_data, 'genre', 'cast', 'director', 'svodEndDate', 'startDate', 'endDate', 'asset',
                        'duration', 'shops', 'country', 'selectedBy', 'poster', 'location', 'startDateMs',
                        'endDateMs', 'tvodPrice', 'tvodSubscribersPrice', obj_name=film_data['title'])
            if 'selectedBy' in film_data.keys():
                self.assertEqual(21, len(tuple(film_data.keys())))
            else:
                self.assertEqual(20, len(tuple(film_data.keys())))

    def test_search_with_no_results(self):
        resp = self.do_search('dfnxjg')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('application/json; charset=UTF-8', resp.headers['content-type'])
        data = json.loads(resp.content)
        results = data['hits']
        self.assertListEqual([], results)