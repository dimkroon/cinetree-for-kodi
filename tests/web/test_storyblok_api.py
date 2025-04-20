
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

from tests.support import object_checks, testutils

import json
import time
from unittest import TestCase

import xbmcplugin

from resources.lib import storyblok
from resources.lib.ctree import ct_api
from resources.lib.ctree import ct_data


token = 'srRWSyWpIEzPm4IzGFBrkAtt'


setUpModule = fixtures.setup_web_test


# noinspection PyMethodMayBeStatic
class StoriesListing(TestCase):
    def test_get_all_stories(self):
        tree = {}
        total_pages = 1
        page = 1
        all_stories  = []

        while page <= total_pages:
            data, headers = storyblok.get_url('stories', params={'page': str(page), 'per_page': 100})
            total_pages = int(headers.get('total')) / 100
            stories = data.get('stories')
            all_stories.extend(stories)
            for story in stories:
                path = story['full_slug'].rstrip('/').split('/')
                item = tree
                for p in path:
                    item = item.setdefault(p, {})
            page += 1
            time.sleep(0.5)
        object_checks.has_keys(tree, 'films', 'shorts', 'thema', 'kids', 'collections', 'curators')
        # print(json.dumps(tree, indent=4))

        # list all used values for component
        components = set()
        for story in all_stories:
            object_checks.has_keys(story['content'], 'component')
            components.add(story['content'].get('component'))
        # print(json.dumps(list(components), indent=4))

    def test_get_rentals(self):
        """Does not return a list of films, but data concerning rentals. Like available filters,
        filter items, a list of preferred collections, etc. Basically, the contents of cinetree's
        page 'huurfilms'

        """
        data, _ = storyblok.get_url('stories/rentals/')
        story = data['story']
        object_checks.check_rentals(story['content'])

    def test_get_all_collections(self):
        data, _ = storyblok.get_url('stories',
                                    params={'starts_with': 'collections/',
                                             'page': 1,
                                             'per_page': 100,
                                             'version': 'published'})
        stories = data.get('stories')
        self.assertIsInstance(stories, list)

        # this does not return a list of collection, only some very uninteresting info about the collections page.
        stories, _ = storyblok.get_url('stories/collections/')
        self.assertNotIsInstance(stories, list)

    def test_get_all_films(self):
        page = 1
        total_pages = 1
        stories = []

        while page <= total_pages:
            data, headers = storyblok.get_url('stories', params={'starts_with': 'films/', 'page': str(page), 'per_page': 100})
            total_pages = int(headers.get('total')) / 100
            stories.extend(data.get('stories'))
            page += 1
            time.sleep(0.05)

        # # Save al stories locally
        # storymap = {story['uuid']: story for story in stories}
        # testutils.save_json(storymap, 'st_blok/films.json')

        for story in stories:
            object_checks.check_film_data(story)

    def test_get_all_shorts(self):
        data, _ = storyblok.get_url('stories', params={'starts_with': 'shorts/', 'page': 1, 'per_page': 100})
        stories = data.get('stories')
        self.assertGreater(len(stories), 0)
        for story in stories:
            object_checks.check_film_data(story)
        # Save al shorts locally
        # storymap = {story['uuid']: story for story in stories}
        # testutils.save_json(storymap, 'st_blok/shorts.json')

    def test_get_all_kids(self):
        data, _ = storyblok.get_url('stories', params={'starts_with': 'kids/', 'page': 1, 'per_page': 100})
        stories = data.get('stories')
        self.assertGreater(len(stories), 0)
        for story in stories:
            object_checks.check_film_data(story)


class FilmListByUuid(TestCase):
    def test_get_list_of_films(self):
        film_uuids = ['de57210e-4fd2-485a-8f1a-26c7caff2a7b', 'ddf98776-1b85-4675-9369-dc646a33a110',
                      'a95b17f6-33fa-4571-93f8-3ad4b794b31d', 'a2a916c7-dd71-4820-b556-2b005c51da10']
        # film_uuids = ['4414d3b2-bb7d-4553-a2ad-6178a59e93ec']
        stories, num_stories = storyblok.stories_by_uuids(film_uuids)
        self.assertIsInstance(stories, list)
        self.assertEqual(num_stories, len(stories))

    def test_get_list_with_a_non_existing_uuid(self):
        """Request a number of films, where only one of the uuid's does not exist.

        Storyblok ignores invalid uuids and just returns a list of films that do exist.

        """
        film_uuids = ['de57210e-4fd2-485a-8f1a-26c7caff2a7b', 'ddf98776-1b85-4675-9369-dc646a33a110',
                      'f00fffff-ffff-0000-0000-ff00ff00ff00', 'a2a916c7-dd71-4820-b556-2b005c51da10']
        # film_uuids = ['4414d3b2-bb7d-4553-a2ad-6178a59e93ec']
        stories, num_stories = storyblok.stories_by_uuids(film_uuids)
        self.assertIsInstance(stories, list)
        self.assertEqual(num_stories, len(film_uuids) -1)

    def test_get_single_film(self):
        stories, num_stories = storyblok.stories_by_uuids('de57210e-4fd2-485a-8f1a-26c7caff2a7b')
        self.assertIsInstance(stories, list)
        self.assertEqual(num_stories, len(stories))
        self.assertEqual(num_stories, 1)

    def test_get_stores_per_page(self):
        film_uuids = ['de57210e-4fd2-485a-8f1a-26c7caff2a7b', 'ddf98776-1b85-4675-9369-dc646a33a110',
                      'a95b17f6-33fa-4571-93f8-3ad4b794b31d', 'a2a916c7-dd71-4820-b556-2b005c51da10']
        # film_uuids = ['4414d3b2-bb7d-4553-a2ad-6178a59e93ec']
        stories_p1, num_stories = storyblok.stories_by_uuids(film_uuids, page=1, items_per_page=2)
        self.assertEqual(num_stories, 4)
        self.assertEqual(len(stories_p1), 2)

        stories_p2, num_stories = storyblok.stories_by_uuids(film_uuids, page=2, items_per_page=2)
        self.assertEqual(num_stories, 4)
        self.assertEqual(len(stories_p2), 2)
        self.assertNotEqual(stories_p1, stories_p2)

        self.assertRaises(ValueError, storyblok.stories_by_uuids, film_uuids, page=1, items_per_page=0)
        self.assertRaises(ValueError, storyblok.stories_by_uuids, film_uuids, page=1, items_per_page=101)

    def test_no_stories(self):
        stories, num_stories = storyblok.stories_by_uuids([])
        self.assertListEqual(stories, [])


# noinspection PyMethodMayBeStatic
class Collections(TestCase):
    def test_get_collection_by_uuid(self):
        collections, num_coll = storyblok.stories_by_uuids('7f7da12a-18cb-4d6a-955d-838cc939de66')
        self.assertEqual(num_coll, len(collections))


class StoryByName(TestCase):
    def test_get_film_by_name(self):
        film_info = storyblok.story_by_name('films/druk')
        self.assertIsInstance(film_info, dict)
        self.assertEqual('Druk', film_info['name'])


class Search(TestCase):
    def test_search_genre(self):
        """Search for all genres"""
        for genre in ct_api.GENRES:
            # print('genre: ', genre)
            film_list, num_films = storyblok.search(genre=genre)
            self.assertEqual(num_films, len(film_list))
            for film in film_list:
                # Fortunately Storyblok appears to do a case-insensitive compare.
                self.assertTrue(genre.lower() in film['content']['genre'].lower())
            # Sleep a short while, so the max number of requests per second to Storyblok is not exceeded.
            time.sleep(0.1)

    def test_search_title(self):
        film_list, num_films = storyblok.search(search_term='is')
        self.assertEqual(num_films, len(film_list))
        for film in film_list:
            self.assertTrue('is' in film['content']['title'].lower(), "Film {} does not contain 'is'".format(film))

    def test_search_country(self):
        film_list, num_films = storyblok.search(country='NL')
        self.assertEqual(num_films, len(film_list))
        for film in film_list:
            self.assertEqual('NL', film['content']['country'],
                             "Film country is not NL , but '{}'".format(film['content']['country']))

    def test_search_duration(self):
        film_list, num_films = storyblok.search(duration_min=60, duration_max=80)
        self.assertEqual(num_films, len(film_list))
        for film in film_list:
            duration = ct_data.FilmItem(film).get_duration() / 60
            self.assertGreater(duration, 60)
            self.assertLess(duration, 80)

    def test_search_duration_as_float(self):
        film_list, num_films = storyblok.search(duration_min=75.3, duration_max=80)
        self.assertEqual(num_films, len(film_list))
        for film in film_list:
            duration = ct_data.FilmItem(film).get_duration() / 60
            self.assertGreater(duration, 75.3)
            self.assertLess(duration, 80)

    def test_invalid_durations(self):
        self.assertRaises(ValueError, storyblok.search, duration_min=-2, duration_max=23)
        self.assertRaises(ValueError, storyblok.search, duration_min=120, duration_max=60)

    def test_search_nothing(self):
        self.assertRaises(ValueError, storyblok.search)

    def test_search_sorted_ascending(self):
        film_list, num_films = storyblok.search(search_term='is',
                                                sort_method=xbmcplugin.SORT_METHOD_TITLE)
        self.assertEqual(num_films, len(film_list))
        prev_title = ''
        for film in film_list:
            # Cinetree sorts case-insensitive and ignores non-alphabetical characters
            title = film['content']['title'].replace(' ', '').replace("'", '').replace(',', '').lower()
            self.assertTrue(title >= prev_title)
            prev_title = title

    def test_search_sorted_decending(self):
        film_list, num_films = storyblok.search(search_term='is',
                                                sort_method=xbmcplugin.SORT_METHOD_TITLE,
                                                sort_order=1)
        self.assertEqual(num_films, len(film_list))
        prev_title = 'zzzzzzzzzz'
        for film in film_list:
            # Cinetree sorts case-insensitive and ignores non-alphabetical characters
            title = film['content']['title'].replace(' ', '').replace("'", '').replace(',', '').lower()
            self.assertTrue(title <= prev_title)
            prev_title = title

    def test_search_sort_on_duration(self):
        film_list, num_films = storyblok.search(genre='Documentary',
                                                sort_method=xbmcplugin.SORT_METHOD_DURATION,
                                                sort_order=0)
        self.assertEqual(num_films, len(film_list))
        prev_duration = 0
        i = 0
        for film in film_list:
            # Cinetree sorts case-insensitive and ignores non-alphabetical characters
            duration = float(film['content']['duration'].split()[0])
            self.assertTrue(duration >= prev_duration)
            prev_duration = duration
            i += 1
