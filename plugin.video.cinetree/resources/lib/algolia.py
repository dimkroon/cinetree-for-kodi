# ------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import time
import logging
import json

import requests
from codequick.support import logger_id

from resources.lib import fetch


logger = logging.getLogger('.'.join((logger_id, __name__)))



def search(search_term):
    if not search_term:
        return []

    now_ms = int(time.time() * 1000)
    url = 'https://ap2sg0z16n-dsn.algolia.net/1/indexes/films/query'
    headers = {
        'x-algolia-api-key': '0fd5e1415555be4cda53a8c870cb665e',
        'x-algolia-application-id': 'AP2SG0Z16N',
        'referer': 'https://www.cintree.nl/',
    }
    form_data = {
        'query': search_term,
        'filters': f'(location:"films" OR location:"shorts") AND startDateMs<={now_ms} AND endDateMs>={now_ms} AND shops:cinetree.nl',
        'disableExactOnAttributes': ['genre'],
        'hitsPerPage': 50}
    resp = requests.post(url, headers=headers, data=json.dumps(form_data))
    results = json.loads(resp.content)['hits']
    uuids = [film['objectID'] for film in results]
    return uuids
