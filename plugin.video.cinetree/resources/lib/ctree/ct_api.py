
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import logging
from enum import Enum

from codequick import Script
from codequick.support import logger_id

from resources.lib import fetch
from resources.lib import errors
from resources.lib import utils
from resources.lib.ctree.ct_data import create_collection_item
from resources.lib import storyblok
from resources.lib.constants import FULLY_WATCHED_PERCENTAGE


STRM_INFO_UNAVAILABLE = 30921

logger = logging.getLogger(logger_id + '.ct_api')
base_url = ''

GENRES = ('Action', 'Adventure', 'Biography', 'Comedy', 'Coming-of-age', 'Crime', 'Drama', 'Documentary',
          'Family', 'Fantasy', 'History', 'Horror', 'Mystery', 'Sci-Fi', 'Romance', 'Thriller')


def get_jsonp_url(slug, force_refresh=False):
    """Append *slug* to the base path for .js requests and return the full url.

    Part of the base url is a unique number (timestamp) that changes every so often. We obtain
    that number from Cinetree's main page and cache it for future requests.

    """
    global base_url

    if not base_url or force_refresh:
        import re

        resp = fetch.get_document('https://cinetree.nl')
        match = re.search(r'href="([\w_/]*?)manifest\.js" as="script">', resp, re.DOTALL)
        base_url = 'https://cinetree.nl' + match.group(1)
        logger.debug("New jsonp base url: %s", base_url)

    url = base_url + slug
    return url


def get_jsonp(path):
    from resources.lib.jsonp import parse, parse_simple

    url = get_jsonp_url(path)
    try:
        resp = fetch.get_document(url)
    except errors.HttpError as err:
        if err.code == 404:
            # Due to reuselanguageinvoker and the timestamp in the path, the path may become
            # invalid if the plugin is active for a long time.
            url = get_jsonp_url(path, force_refresh=True)
            resp = fetch.get_document(url)
            # Although the timestamps are not the same, expect storyblok's cache version to have been updated as well
            storyblok.clear_cache_version()
        else:
            raise

    if '__NUXT_' in resp[:16]:
        resp_dict = parse(resp)
    else:
        resp_dict = parse_simple(resp)
    return resp_dict


def get_recommended():
    """Return the uuids of the hero items on the subscription page"""
    data, _ = storyblok.get_url('stories//films-en-documentaires',
                                params={'from_release': 'undefined', 'resolve_relations': 'menu,selectedBy'})
    page_top = data['story']['content']['top']
    for section in page_top:
        if section['component'] == 'row-featured-films':
            return section['films']
    return []


def get_subscription_films():
    """Return a list of ID's of the current subscription films"""
    resp = fetch.get_json('https://api.cinetree.nl/films/svod')
    return resp


def create_stream_info_url(film_uuid, slug=None):
    """Return the url to the stream info (json) document.

    Create the url from the uuid. If the uuid is not available, obtain the
    uuid from the film's details page.

    """
    if not film_uuid:
        try:
            data = storyblok.story_by_name(slug)
            film_uuid = data['uuid']
        except (errors.FetchError, TypeError, KeyError):
            logger.error("Unable to obtain uuid from film details of '%s'.", slug, exc_info=True)
            raise errors.FetchError(Script.localize(STRM_INFO_UNAVAILABLE))

    url = 'https://api.cinetree.nl/films/' + film_uuid
    return url


def get_stream_info(url):
    """Return a dict containing urls to the m3u8 playlist, subtitles, etc., for a specific
    film or trailer.

    """
    data = fetch.fetch_authenticated(fetch.get_json, url)
    return data


def get_subtitles(url: str, lang: str) -> str:
    """Download vtt subtitles file, convert it to srt and save it locally.
    Return the full path to the local file.

    """
    if not url:
        return ''

    vtt_titles = fetch.get_document(url)
    # with open(utils.get_subtitles_temp_file().rsplit('.', 1)[0] + '.vtt', 'w', encoding='utf8') as f:
    #     f.write(vtt_titles)
    srt_titles = utils.vtt_to_srt(vtt_titles)
    logger.debug("VTT subtitles of length %s converted to SRT of length=%s.", len(vtt_titles), len(srt_titles))
    subt_file = utils.get_subtitles_temp_file(lang)
    with open(subt_file, 'w', encoding='utf8') as f:
        f.write(srt_titles)
    return subt_file


def get_watched_films(finished=False):
    """Get the list of 'Mijn Films' to continue watching

    """
    # Request the list of 'my films' and use only those that have only partly been played.
    history = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/watch-history')
    # history = {film['assetId']: film for film in history if 'playtime' in film.keys()}
    sb_films, _ = storyblok.stories_by_uuids(film['assetId'] for film in history)
    sb_films = {film['uuid']: film for film in sb_films}

    finished_films = []
    watched_films = []

    for item in history:
        try:
            film = sb_films[item['assetId']]
            duration = utils.duration_2_seconds(film['content'].get('duration', 0))
            playtime = item['playtime']
            # Duration seems to be rounded up to whole minutes, so actual playing time could
            # still differ by 60 seconds when the video has been fully watched.
            if duration - playtime < max(60, duration * (1-FULLY_WATCHED_PERCENTAGE)):
                finished_films.append(film)
            else:
                watched_films.append(film)
        except KeyError:
            # Field playtime may be absent. These items are also disregarded by a regular web browser.
            # And defend against the odd occurrence that a watched film is no longer in the storyblok database.
            logger.debug('Error ct_api.get_watched_films:\n', exc_info=True)
            continue
    return finished_films if finished else watched_films


def remove_watched_film(film_uuid):
    """Remove a film from the watched list.

    It seems that after removing a film will not be added when watched again.

    At the time of testing every request, either with existing, or non-existing
    UUID, or existing films not on the list, return without error.

    """
    resp = fetch.fetch_authenticated(fetch.web_request,
                                     method='delete',
                                     url='https://api.cinetree.nl/watch-history/by-asset/' + film_uuid)
    return resp.status_code == 200


def get_rented_films():
    resp = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/purchased')
    # contrary to watched, this returns a plain list of uuids
    if resp:
        rented_films, _ = storyblok.stories_by_uuids(resp)
        return rented_films
    else:
        return resp


def get_preferred_collections():
    """Get a short list of the currently preferred collection.

    This is a short selection of all available collections that the user gets
    presented on the website when he clicks on 'huur films'
    """
    data = get_jsonp('films/payload.js')['fetch']
    for k, v in data.items():
        if k.startswith('data-v'):
            return (create_collection_item(col_data) for col_data in v['collections'])


def get_collections():
    """Get a list of all available collections
    Which, by the way, are not exactly all collections, but those the website shows as 'all'.
    To get absolutely all collections, request them from storyblok.
    """
    data = get_jsonp('collecties/payload.js')
    return (create_collection_item(col_data) for col_data in data['data'][0]['collections'])


class DurationFilter(Enum):
    MAX_1_HR = 60
    BETWEEN_1_TO_2_HRS = 120
    MORE_THAN_2_HRS = 500


def search_films(search_term='', genre=None, country=None, duration=None):
    """Perform a search using the Cinetree api

    Search_term searches on multiple fields, like title, cast, etc.

    """
    # Without args Cinetree returns a lot of items, probably all films, which is not
    # what we want.
    if not any((search_term, genre, country, duration)):
        return []

    query = {'q': search_term, 'startsWith': 'films/,kids/,shorts/'}
    if genre:
        query['genre'] = genre.lower()
    if country:
        query['country'] = country
    if duration:
        query['duration[]'] = {60: ['0', '59'],
                               120: ['60', '120'],
                               500: ['121', '500']}[duration]
    return fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/films', params=query)


def set_resume_time(watch_history_id: str, play_time: float):
    """Report the play position back to Cinetree.

    """
    url = 'https://api.cinetree.nl/watch-history/{}/playtime'.format(watch_history_id)
    play_time = round(play_time, 3)
    data = {"playtime": play_time}
    try:
        fetch.fetch_authenticated(fetch.put_json, url, data=data)
    except Exception as e:
        logger.warning('Failed to report resume time to Cinetree: %r', e)
        return
    logger.debug("Playtime %s reported to Cinetree", play_time)


def get_payment_info(film_uid: str):
    """Return a tuple of the transaction id and amount to be paid to
    rent a film.

    """
    url = 'https://api.cinetree.nl/payments/info/rental/' + film_uid
    payment_data = fetch.fetch_authenticated(fetch.post_json, url, data=None)
    return float(payment_data['amount']), payment_data['transaction']


def get_ct_credits():
    """Return the current amount of available cinetree credits

    """
    my_data = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/me')
    return float(my_data['credit'])


# noinspection PyBroadException
def pay_film(film_uid, film_title, transaction_id, price):
    try:
        payment_data = {
            'context': {
                'trackEvents': [
                    {
                        'event': 'purchase',
                        'params': {
                            'ecommerce': {
                                'currency': 'EUR',
                                'items': [
                                    {
                                        'item_category': 'TVOD',
                                        'item_id': film_uid,
                                        'item_name': film_title,
                                        'price': price,
                                        'quantity': 1
                                    }
                                ],
                                'tax': price - price / 1.21,
                                'transaction_id': transaction_id,
                                'value': price
                            }
                        }
                    }
                ]
            },
            'transaction': transaction_id
        }
        resp = fetch.fetch_authenticated(
            fetch.web_request,
            'https://api.cinetree.nl/payments/credit',
            method='post',
            headers={'Accept': 'application/json, text/plain, */*'},
            data=payment_data
        )
        content = resp.content.decode('utf8')
        if content:
            logger.warning("[pay_film] - Unexpected response content: '%s'", content)
        # On success cinetree returns 200 OK without content.
        if resp.status_code == 200:
            logger.info("[pay_film] Paid %0.2f from cinetree credit for film '%'")
            return True
        else:
            logger.error("[pay_film] - Unexpected response status code: '%s'", resp.status_code)
            return False
    except:
        logger.error("[pay_film] paying failed: film_uid=%s, film_title=%s, trans_id=%s, price=%s\n",
                     film_uid, film_title, transaction_id, price, exc_info=True)
        return False
