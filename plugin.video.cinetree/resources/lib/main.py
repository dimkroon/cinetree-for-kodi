
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import xbmcplugin
import sys
from collections.abc import Iterable

from xbmc import executebuiltin
from xbmcgui import ListItem as XbmcListItem

from codequick import Route, Resolver, Listitem, Script
from codequick import run as cc_run

from resources.lib.addon_log import logger
from resources.lib.ctree import ct_api
from resources.lib.ctree import ct_data
from resources.lib import storyblok, kodi_utils
from resources.lib import errors
from resources.lib import constants
from resources.lib import watchlist


logger.critical('-------------------------------------')


MSG_FILM_NOT_AVAILABLE = 30606
MSG_ONLY_WITH_SUBSCRIPTION = 30607
TXT_MY_FILMS = 30801
TXT_RECOMMENDED = 30802
TXT_MONTH_SELECTION = 30803
TXT_RENTALS_COLLECTIONS = 30805
TXT_RENTALS_GENRES = 30806
TXT_SEARCH = 30807
TXT_ALREADY_WATCHED = 30808
TXT_RENTED = 30809
TXT_ALL_COLLECTIONS = 30810
TXT_CONTINUE_WATCHING = 30811
TXT_MY_LIST = 30812
TXT_REMOVE_FROM_LIST = 30859
TXT_NOTHING_FOUND = 30608
TXT_TOO_MANY_RESULTS = 30609
MSG_PAYMENT_FAIL = 30625
MSG_REMOVE_CONFIRM = 30626
MSG_REMOVED_TITLES = 30627


@Route.register
def root(_):
    yield Listitem.from_dict(list_my_films, Script.localize(TXT_MY_FILMS), params={'_cache_to_disc_': False})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_RECOMMENDED),
                             params={'category': 'recommended'})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_MONTH_SELECTION),
                             params={'category': 'subscription'})
    yield Listitem.from_dict(list_rental_collections, Script.localize(TXT_RENTALS_COLLECTIONS))
    yield Listitem.from_dict(list_genres, Script.localize(TXT_RENTALS_GENRES))
    yield Listitem.search(do_search, Script.localize(TXT_SEARCH))


@Route.register(content_type='movies')
def list_my_films(addon, subcategory=None):
    """List the films not finished watching. Newly purchased films appear here, so do not cache"""

    if subcategory is None:
        yield Listitem.from_dict(list_watchlist,
                                 Script.localize(TXT_MY_LIST),
                                 params={'_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_CONTINUE_WATCHING),
                                 params={'subcategory': 'continue', '_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_RENTED),
                                 params={'subcategory': 'purchased', '_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_ALREADY_WATCHED),
                                 params={'subcategory': 'finished', '_cache_to_disc_': False})
        return

    if subcategory == 'purchased':
        list_name = None
        films = ct_data.create_films_list(ct_api.get_rented_films(), 'storyblok')
    else:
        watched_films = ct_api.get_watched_films()
        if subcategory == 'finished':
            list_name = TXT_ALREADY_WATCHED
            films = (film for film in watched_films if film.playtime >= film.duration)
        else:
            list_name = TXT_CONTINUE_WATCHING
            films = (film for film in watched_films if film.playtime < film.duration)

    if not films:
        # yield False
        return
    wl = watchlist.WatchList()

    for film in films:
        uuid = film.uuid
        li = Listitem.from_dict(callback=play_film, **film.data)
        if list_name:
            li.context.script(remove_from_list,
                              addon.localize(TXT_REMOVE_FROM_LIST).format(listname=list_name),
                              film_uuid=uuid,
                              title=film.data['info']['title'])
        watchlist.create_ctx_mnu(li, film, wl)
        yield li


def _create_playables(films: Iterable[ct_data.FilmItem]):
    """Create playable Codequick.Listitems from FilmItems with a
    context menu items to add or remove from Watch List.

    """
    wl = watchlist.WatchList()
    creat_ctx = watchlist.create_ctx_mnu
    for film_item in films:
        if film_item:
            li = Listitem.from_dict(callback=play_film, **film_item.data)
            creat_ctx(li, film_item, wl)
            yield li
        else:
            logger.debug("film item is Empty")


@Route.register(content_type='movies')
def list_watchlist(addon):
    addon.add_sort_methods(xbmcplugin.SORT_METHOD_DATEADDED)
    with watchlist.WatchList() as wl:
        films_list, _ = storyblok.stories_by_uuids(wl.keys())
        films = {}
        for film in films_list:
            film_item = ct_data.FilmItem(film)
            if not film_item:
                continue
            film_item.data['info']['dateadded'] = wl[film_item.uuid]['added']
            films[film_item.uuid] = film_item
        # Check which films are no longer available
        removed_titles = ['']
        for uuid, wl_data in tuple(wl.items()):
            if uuid not in films:
                del wl[uuid]
                removed_titles.append(wl_data['title'])
    if len(removed_titles) > 1:
        titles_list = '\n- '.join(removed_titles)
        kodi_utils.ok_dialog(addon.localize(MSG_REMOVED_TITLES).format(titles=titles_list))
    return _create_playables(films.values())


@Route.register(content_type='movies')
def list_films_and_docus(_, category):
    """List subscription films"""
    if category == 'subscription':
        film_ids = ct_api.get_subscription_films()
    elif category == 'recommended':
        film_ids = ct_api.get_recommended()
    else:
        return None
    stories, _ = storyblok.stories_by_uuids(film_ids)
    films = ct_data.create_films_list(stories, 'storyblok', add_price=False)
    return list(_create_playables(films))


@Route.register()
def list_rental_collections(addon):
    collections = ct_api.get_preferred_collections()
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)
    yield Listitem.from_dict(list_all_collections, addon.localize(TXT_ALL_COLLECTIONS))


@Route.register()
def list_all_collections(_):
    collections = ct_api.get_collections()
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)


@Route.register()
def list_genres(_):
    for genre in ct_api.GENRES:
        yield Listitem.from_dict(list_films_by_genre, label=genre, params={'genre': genre})


@Route.register()
def do_search(_, search_query):
    uuids = ct_api.search_films(search_term=search_query)

    if len(uuids) > 100:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_TOO_MANY_RESULTS),
                      Script.NOTIFY_INFO, 12000)

    stories, _ = storyblok.stories_by_uuids(uuids[:100])

    if stories:
        films = ct_data.create_films_list(stories, 'storyblok')
        return list(_create_playables(films))
    else:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_NOTHING_FOUND),
                      Script.NOTIFY_INFO, 7000)
        return False


@Route.register(content_type='movies')
def list_films_by_collection(_, slug):
    data = ct_api.get_jsonp(slug + '/payload.js')
    yield from _create_playables(ct_data.create_films_list(data))


@Route.register(content_type='movies')
def list_films_by_genre(_, genre, page=1):
    list_len = 50
    films, num_films = storyblok.search(genre=genre, page=page, items_per_page=list_len)
    yield from _create_playables(ct_data.FilmItem(film) for film in films)
    if num_films > page * list_len:
        yield Listitem.next_page(genre=genre, page=page + 1)


@Script.register()
def remove_from_list(addon, film_uuid, title):
    """Remove a film from the 'Continue Watching' or 'Already Watched' list."""
    if kodi_utils.yes_no_dialog(addon.localize(MSG_REMOVE_CONFIRM).format(title=title)):
        ct_api.remove_watched_film(film_uuid)
        logger.info("Removed film '%s' from the watched list", title)
        executebuiltin('Container.Refresh')
    else:
        logger.debug("Remove film '%s' canceled by user.", title)


def monitor_progress(watch_id):
    """Pushes playtime to Cinetree when playing starts and when playing ends.

    Is being run after a playable item has been returned to Kodi.
    """
    player = kodi_utils.PlayTimeMonitor()
    if player.wait_until_playing(10) is False:
        return
    ct_api.set_resume_time(watch_id, player.playtime)
    player.wait_while_playing()
    ct_api.set_resume_time(watch_id, player.playtime)


def create_hls_item(url, title):
    # noinspection PyImport,PyUnresolvedReferences
    import inputstreamhelper

    PROTOCOL = 'hls'

    is_helper = inputstreamhelper.Helper(PROTOCOL)
    if not is_helper.check_inputstream():
        logger.warning('No support for protocol %s', PROTOCOL)
        return False

    play_item = XbmcListItem(title, offscreen=True)
    if title:
        play_item.setInfo('video', {'title': title})

    play_item.setPath(url)
    play_item.setContentLookup(False)

    stream_headers = ''.join((
            'User-Agent=',
            constants.USER_AGENT,
            '&Referer=https://www.cinetree.nl/&'
            'Origin=https://www.cinetree.nl&'
            'Sec-Fetch-Dest=empty&'
            'Sec-Fetch-Mode=cors&'
            'Sec-Fetch-Site=same-site'))

    play_item.setProperties({
        'IsPlayable': 'true',
        'inputstream': 'inputstream.adaptive',
        'inputstream.adaptive.manifest_type': PROTOCOL,
        'inputstream.adaptive.stream_headers': stream_headers
    })

    return play_item


def play_ct_video(stream_info: dict, title: str = ''):
    """ From the info provided in *stream_info*, prepare subtitles and build
    a playable xbmc.ListItem to play a film, short film, or trailer
    from Cinetree.

    """
    try:
        subtitles = [ct_api.get_subtitles(url, lang) for lang, url in stream_info['subtitles'].items()]
        logger.debug("using subtitles '%s'", subtitles)
    except KeyError:
        logger.debug("No subtitels available for video '%s'", title)
        subtitles = None
    except errors.FetchError as e:
        logger.error("Failed to fetch subtitles: %r", e)
        subtitles = None

    play_item = create_hls_item(stream_info.get('url'), title)
    if play_item is False:
        return False

    if subtitles:
        play_item.setSubtitles(subtitles)

    # Resume from 10 sec before the actual play time, so it's easier to pick up from where we've left off.
    resume_time = max(0, int(stream_info.get('playtime', 0)) - 10)
    duration = int(stream_info.get('duration', 0))
    if 0 < resume_time < duration * constants.FULLY_WATCHED_PERCENTAGE:
        result = kodi_utils.ask_resume_film(resume_time)
        logger.debug("Resume from %s result = %s", resume_time, result)
        if result == -1:
            logger.debug("User canceled resume play dialog")
            return False
        elif result == 0:
            play_item.setInfo('video', {'playcount': '1'})
            play_item.setProperties({
                'ResumeTime': str(resume_time),
                'TotalTime': str(duration)
            })
            logger.debug("Play from %s", resume_time)
        else:
            logger.debug("Play from start")

    return play_item


@Resolver.register
def play_film(plugin, title, uuid, slug):
    logger.info('play film - title=%s, uuid=%s, slug=%s', title, uuid, slug)
    try:
        stream_info = ct_api.get_stream_info(ct_api.create_stream_info_url(uuid, slug))
        logger.debug("play_info = %s", stream_info)
    except errors.NotPaidError:
        if pay_from_ct_credit(title, uuid):
            return play_film(plugin, title, uuid, slug)
        else:
            return False
    except errors.NoSubscriptionError:
        Script.notify('Cinetree', Script.localize(MSG_ONLY_WITH_SUBSCRIPTION), Script.NOTIFY_INFO, 6500)
        return False
    except errors.FetchError as err:
        status_code = getattr(err, 'code', None)
        if status_code == 404:
            Script.notify('Cinetree', Script.localize(MSG_FILM_NOT_AVAILABLE), Script.NOTIFY_INFO, 6500)
        else:
            logger.error('Error retrieving film urls: %r' % err)
            Script.notify('Cinetree', str(err), Script.NOTIFY_ERROR, 6500)
        return False
    except Exception as e:
        logger.error('Error playing film: %r' % e, exc_info=True)
        return False

    play_item = play_ct_video(stream_info, title)
    if play_item:
        plugin.register_delayed(monitor_progress, watch_id=stream_info.get('watchHistoryId'))
    return play_item


@Resolver.register
def play_trailer(plugin, url):
    if 'youtube' in url:
        logger.info("Play youtube trailer: '%s'", url)
        return plugin.extract_source(url)

    if 'vimeo' in url:
        from resources.lib.vimeo import get_steam_url
        url_type, stream_url = get_steam_url(url)
        if url_type == 'file':
            logger.info("Play vimeo file trailer: '%s'", stream_url)
            return stream_url
        elif url_type == 'hls':
            logger.info("Play vimeo HLS trailer: '%s'", stream_url)
            return create_hls_item(stream_url, 'trailer')

    if 'cinetree' in url:
        stream_info = ct_api.get_stream_info(url)
        logger.info("Play cinetree trailer: '%s'", stream_info.get('url'))
        return play_ct_video(stream_info, 'trailer')

    logger.warning("Cannot play trailer from unknown source: '%s'.", url)
    return False


def pay_from_ct_credit(title, uuid):
    from concurrent import futures
    executor = futures.ThreadPoolExecutor()
    future_objs = [executor.submit(ct_api.get_payment_info, uuid),
                   executor.submit(ct_api.get_ct_credits)]
    futures.wait(future_objs)
    amount, trans_id = future_objs[0].result()
    ct_credits = future_objs[1].result()
    if amount > ct_credits:
        kodi_utils.show_low_credit_msg(amount, ct_credits)
    elif kodi_utils.confirm_rent_from_credit(title, amount, ct_credits):
        if ct_api.pay_film(uuid, title, trans_id, amount):
            return True
        else:
            kodi_utils.ok_dialog(MSG_PAYMENT_FAIL)
    return False


def run():
    if isinstance(cc_run(), Exception):
        xbmcplugin.endOfDirectory(int(sys.argv[1]), False)
