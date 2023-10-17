

# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import requests
import unittest

from tests.support import fixtures
fixtures.global_setup()

from tests.support import testutils, object_checks

from resources.lib import fetch
from resources.lib import errors
from resources.lib import storyblok
from resources.lib.ctree import ct_api


setUpModule = fixtures.setup_web_test


class Login(unittest.TestCase):
    def test_login_with_invalid_credentials(self):
        credentials = {'username': 'paraflkfjh', 'password': 'dl48y09ijm'}
        resp = requests.post('https://api.cinetree.nl/login', json=credentials)
        self.assertEqual(401, resp.status_code)
        resp_data = resp.json()
        self.assertEqual('Invalid username', resp_data['message'])

    def test_login_with_valid_user_but_invalid_password(self):
        try:
            import account_login
        except ImportError:
            unittest.skip('account_login.py not present')
            return

        credentials = {'username': account_login.UNAME, 'password': 'dl48y09ijm'}
        resp = requests.post('https://api.cinetree.nl/login', json=credentials)
        self.assertEqual(401, resp.status_code)
        resp_data = resp.json()
        self.assertEqual('Invalid password', resp_data['message'] )


# noinspection PyMethodMayBeStatic
class Films(unittest.TestCase):
    """Get main huurfilms payload.js"""

    def test_huurfilms_payload(self):
        resp = ct_api.get_jsonp('films/payload.js')
        # Is the same object as returned by stories/rentals on storyblok.com.
        object_checks.check_rentals(resp['data'][0]['story']['content'])

    def test_huurfilms_with_expired_timestamp(self):
        with self.assertRaises(errors.HttpError) as er:
            fetch.get_document('https://cinetree.nl/_nuxt/static/1658984774/films/payload.js')
        self.assertEqual(404, er.exception.code)


# noinspection PyMethodMayBeStatic
class GetStreamsOfFilm(unittest.TestCase):
    """Obtain a json object containing urls to m3u8 playlists and subtitles, etc.
    i.e. info required to play the film.

    Stream info is only accessible for films for which the user has authorisation.
    That are films in the monthly subscription and films that have been rented.
    Other films return a http error 401 - not authorized.

    """
    def test_stream_info_from_free_film(self):
        """Request ino of free film 'For Sama'."""
        url ='https://api.cinetree.nl/films/8b9d9b9d-0865-4b44-bfcf-529fadff0efe'
        resp = fetch.fetch_authenticated(fetch.get_json, url)
        object_checks.check_stream_info(resp)
        # optionally store the content for use in local tests
        # with open('../test_docs/stream_info.json', 'w') as f:
        #     json.dump(resp, f)

    def test_stream_info_without_subscription(self):
        # Ensure to select a currently available film from the subscription
        resp = ct_api.get_jsonp('films-en-documentaires/payload.js')['fetch']
        uuid = None
        full_slug = None

        for item in resp.values():
            f_list = item.get('films')
            if not f_list or len(f_list) > 4:
                continue

            uuid = f_list[0]['uuid']
            full_slug = f_list[0]['full_slug']
            break

        # Get info by film uuid, should succeed
        url = 'https://api.cinetree.nl/films/' + uuid
        self.assertRaises(errors.NoSubscriptionError, fetch.fetch_authenticated, fetch.get_json, url)

    def test_stream_info_from_not_paid_rentable_uuid(self):
        """Request info of 'girlhood'. Ensure this film is not currently being rented.
        Rental films return AccessRestrictError when they have not been rented."""
        url = 'https://api.cinetree.nl/films/de57210e-4fd2-485a-8f1a-26c7caff2a7b'
        self.assertRaises(errors.NotPaidError, fetch.fetch_authenticated, fetch.get_json, url)

    def test_stream_info_from_unavailable_film(self):
        # film 'prisoner', which has an end_date in the past
        url = 'https://api.cinetree.nl/films/1870b1f3-9ffe-4742-b4ae-00278cddf344'
        self.assertRaises(errors.HttpError, fetch.fetch_authenticated, fetch.get_json, url)


class Genres(unittest.TestCase):
    """Try get a listing of available genres"""
    def test_get_genres(self):
        # Genres does not exist
        with self.assertRaises(errors.HttpError):
            fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/genres/')

    def test_get_genre(self):
        # Genre doesn't exist either
        with self.assertRaises(errors.HttpError):
            fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/genre')

    def test_get_genres_from_films_payload(self):
        """films/paylaod has a field 'filterGenreItems' with contains a comma separated list of all
        available genres.
        """
        resp = ct_api.get_jsonp('films/payload.js')
        # Assert genres are up-to-date
        genres = set(resp['data'][0]['story']['content']['filterGenreItems'].split(','))
        self.assertEqual(set(ct_api.GENRES), genres), "Genres list has been changed to {}".format(genres)


class FilmsInGenre(unittest.TestCase):
    def test_genre_comedy_as_from_browser(self):
        """Request all films in genre comedy,
        Returns a list of uuid's
        """
        film_data = fetch.fetch_authenticated(
            fetch.get_json, 'https://api.cinetree.nl/films?q=&genre=comedy&startsWith=films/,kids/')
        self.assertIsInstance(film_data, list)
        # assert there are not duplicates in the returned lists
        film_set = set(film_data)
        self.assertEqual(len(film_data), len(film_set))

    def test_genre_comedy_plain(self):
        # return 2 more items than the url above including 'startsWith'
        film_data = fetch.fetch_authenticated(
            fetch.get_json, 'https://api.cinetree.nl/films?q=&genre=comedy')
        self.assertIsInstance(film_data, list)
        # assert there are not duplicates in the returned lists
        film_set = set(film_data)
        self.assertEqual(len(film_data), len(film_set))

    def test_difference_between_plain_and_films_kids(self):
        """Check what exactly are the extra items when not filtered on films and kids"""
        full = set(fetch.fetch_authenticated(
            fetch.get_json, 'https://api.cinetree.nl/films?q=&genre=comedy'))
        filtered = set(fetch.fetch_authenticated(
            fetch.get_json, 'https://api.cinetree.nl/films?q=&genre=comedy&startsWith=films/,kids/'))

        same_items = full.intersection(filtered)
        different_items = full.difference(filtered)
        self.assertEqual(len(same_items) + len(different_items), len(full))
        same_films, _ = storyblok.stories_by_uuids(same_items)
        different_films, _ = storyblok.stories_by_uuids(different_items)
        # assert that all listed uuid return an actual film
        self.assertEqual(len(same_films), len(same_items))
        self.assertEqual(len(different_films), len(different_items))

        print("Extra films when not filtered with 'startsWith=films/,kids/':", *different_films, sep='\n')


class FilterFilms(unittest.TestCase):
    def test_filter_duration_less_than_60_min(self):
        film_data = fetch.fetch_authenticated(
            # url exactly as browser
            fetch.get_json, 'https://api.cinetree.nl/films?q=&duration[]=0&duration[]=59&startsWith=films/,kids/'
        )
        self.assertIsInstance(film_data, list)
        for item in film_data:
            self.assertTrue(testutils.is_uuid(item))


# noinspection PyMethodMayBeStatic
class FetchSubtitles(unittest.TestCase):
    def test_get_subtitles_of_a_trailer(self):
        resp = fetch.web_request("GET", 'https://api.cinetree.nl/streams/qrYDt5daX6I2MRChibpwZ3UCsFOag3OMqNHOfVINmdI/1658896580460/5b96cdce4c084e000d7abab4/subtitles/nl.vtt')
        resp.encoding = 'utf8'
        resp.raise_for_status()
        # with open('test_docs/subtitle-trialer-la_grande_bellezza.vtt', 'w') as f:
        #     f.write(resp.text)
        # pass

    def test_get_subtitles_of_a_film(self):
        resp = fetch.web_request("GET", 'https://api2.cinetree.nl/streams/FW40fxU_7UVfGWV1vA8_WM5HqMwX-hvvcEkwnYU0wlE/1658901386329/62d79c4bfc3474f05c02ef9c/subtitles/nl.vtt')
        resp.encoding = 'utf8'
        resp.raise_for_status()
        # with open('test_docs/subtitle-film-you_were_never_really_here.vtt', 'w') as f:
        #     f.write(resp.text)
        # pass
