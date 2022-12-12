
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import unittest

from tests.support import fixtures
fixtures.global_setup()


import time
from unittest import TestCase

from resources.lib import storyblok
from resources.lib.ctree import ct_api


setUpModule = fixtures.setup_web_test


@unittest.skip
class Compare(TestCase):
    def test_title_search(self):
        """Storyblok search is much faster than Cinetree, but Cinetree returns better matches.

        """
        query = 'love'
        # Ensure cache_version of storyblok is set
        storyblok.stories_by_uuids('de57210e-4fd2-485a-8f1a-26c7caff2a7b')
        start_t = time.monotonic()
        sb_items, _ = storyblok.search(search_term=query)
        sb_time = time.monotonic() - start_t
        start_t = time.monotonic()
        ct_uuids = set(ct_api.search_films(search_term=query))
        ct_time = time.monotonic() - start_t
        ct_items, _ = storyblok.stories_by_uuids(ct_uuids)
        print('Search time:', 'cinetree: {}'.format(ct_time), 'storyblok {}'.format(sb_time), sep='\n')
        sb_uuids = set([item['uuid'] for item in sb_items])
        self.assertIsInstance(sb_items, list)

        in_sb_and_not_in_ct = sb_uuids.difference(ct_uuids)
        print("\nFilms in Storyblok, but not in Cinetree:")
        print(*('{} - {}'.format(film['content'].get('title', 'NO TITLE'), film) for film in sb_items if film['uuid'] in in_sb_and_not_in_ct), sep='\n')

        in_ct_and_not_in_sb = ct_uuids.difference(sb_uuids)
        print("\nFilms in Cinetree, but not in Storyblok:")
        print(*(film['content']['title'] for film in ct_items if film['uuid'] in in_ct_and_not_in_sb), sep='\n')

        in_both = ct_uuids.intersection(sb_uuids)
        print("\nFilms present in both Cinetree and Storyblok:")
        print(*(film['content']['title'] for film in ct_items if film['uuid'] in in_both), sep='\n')

        for film in (film for film in sb_items if film['uuid'] in in_sb_and_not_in_ct):
            find_search_term(film, query)


def search_item(item, search_val, path):
    if isinstance(item, str):
        if search_val in item.lower():
            print(path)
            return True
        else:
            return False
    elif isinstance(item, dict):
        return traverse_dict(item, search_val, path)
    elif isinstance(item, list):
        return traverse_list(item, search_val, path)
    else:
        # other types , like bool, int, etc
        return False


def traverse_dict(dict_obj, search_val, path=''):
    result = False
    for k, v in dict_obj.items():
        new_path = path + '.' + k
        result |= search_item(v, search_val, new_path)
    return result


def traverse_list(list_obj, search_val, path=''):
    result = False
    for i in range(len(list_obj)):
        item = list_obj[i]
        new_path = '{}[{}]'.format(path, i)
        result |= search_item(item, search_val, new_path)
    return result


def find_search_term(data_obj, search_term):
    print("\nFind '{}' in {}".format(search_term.lower(), data_obj['content'].get('title', 'NO TITLE')))
    if not traverse_dict(data_obj, search_term.lower(), '    '):
        print('    NOTHING FOUND')
