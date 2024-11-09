

# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import time

from resources.lib.ctree import ct_api


def has_keys(dict_obj, *keys, obj_name='dictionary'):
    """Checks if all keys are present in the dictionary"""
    keys_set = set(keys)
    present_keys = set(dict_obj.keys()).intersection(keys_set)
    if present_keys != keys_set:
        absent = keys_set.difference(present_keys)
        raise AssertionError("Key{} {} {} not present in '{}'".format(
            's' if len(absent) > 1 else '',
            absent,
            'is' if len(absent) == 1 else 'are',
            obj_name)
        )


def check_stream_info(strm_inf, additional_keys=None):
    """Check the structure of a dictionary containing urls to playlist and subtitles, etc."""
    mandatory_keys = {'watchHistoryId', 'url', 'subtitles', 'type', 'duration'}
    if additional_keys:
        mandatory_keys.update(additional_keys)
    has_keys(strm_inf, *mandatory_keys)
    url = strm_inf['url']
    assert url.startswith('https://'), "Not a valid playlist url: <{}>".format(strm_inf['url'])
    assert url.endswith('.m3u8') or '.m3u8?' in url, "Not a valid playlist url: <{}>".format(strm_inf['url'])
    assert isinstance(strm_inf['watchHistoryId'], str), \
        "Unexpected type of watchHistoryId: {}".format(type(strm_inf['watchHistoryId']))
    assert isinstance(strm_inf['subtitles'], dict), \
        "subtitles is of unexpected type {}".format(type(strm_inf['subtitles']))
    if len(strm_inf['subtitles']):
        # Assure there is at least Dutch subtitles, if any, and that it is of .vtt type.
        assert 'nl' in strm_inf['subtitles'].keys(), "No Dutch subtitles available"
        assert strm_inf['subtitles']['nl'].startswith('https://'), \
            "Not a valid subtitle url: <{}>".format(strm_inf['url'])
        assert strm_inf['subtitles']['nl'].endswith('.vtt'), \
            "Expected .vtt subtitle format, but found '{}'".format(strm_inf['subtitles']['nl'])
    duration = strm_inf['duration']
    assert(isinstance(duration, float) and duration > 0)

def check_film_data(film_info, additional_content_keys=None):
    """Check that a film info object retrieved from the web meets expectations"""
    mandatory_content_keys = {'poster', 'background', 'blocks', 'title'}
    if additional_content_keys:
        mandatory_content_keys.update(additional_content_keys)

    has_keys(film_info, 'full_slug', 'content', obj_name='film-info-obj')

    assert isinstance(film_info, dict), "Film info object is not a dict, but {}".format(type(film_info))

    content = film_info['content']
    title = '{}.content'.format(content.get('title', 'film-info-obj'))
    # Note: field 'component' is missing in films returned by films_en_docus-payload.js.
    if content.get('component') not in ('film', None):
        print("WARNING: {}.component is not 'film', but '{}'".format(title, content.get('component')))
        return

    has_keys(content, *mandatory_content_keys, obj_name=title)

    # if cast is present check that the parser can split on comma
    # NOTE: In documents retrieved from Cinetree the space is occasionally a non-breaking-space character.
    cast = content.get('cast')
    if cast:
        assert cast.find('\\,') < 0, "Backslash escaped comma found in {}".format(title + '.cast')

    # if genre is present check that the parser can split on comma
    genres = content.get('genre')
    if genres:
        assert genres.find('\\,') < 0, "Backslash escaped comma found in {}".format(title + '.genres')

    # if originalTrailer is present check the presence of keys
    orig_trailer = content.get('originalTrailer')
    if orig_trailer:
        has_keys(orig_trailer, 'selected', 'plugin', obj_name=title + '.originalTrailer')
        assert 'cinetree-autocomplete' == orig_trailer['plugin'], \
            "Expected plugin type 'cinetree-autocomplete', found {}; in {}".format(
                orig_trailer['plugin'], title + '.originalTitle')
        assert isinstance(orig_trailer['selected'], (str, type(None)))

    orig_trail_url = content.get('originalTrailerURL', '').strip()
    if orig_trail_url:
        assert(orig_trail_url.startswith('https://'))

    # assert svodEndDate is of the right format, if present
    svod_end_date = content.get('svodEndDate')
    if svod_end_date:
        try:
            time.strptime(svod_end_date, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                svod_end_time = time.strptime(svod_end_date, "%Y-%m-%d")
            except ValueError:
                raise AssertionError(
                    "Unexpected format of svodEndDate '{}' in {}, expected '%Y-%m-%d %H:%M'".format(svod_end_date, title)
                ) from None
            else:
                # This unsupported format is frequently found in older films, but they have long expired anyway.
                if svod_end_time.tm_year > 2020:
                    raise AssertionError(
                        "Unsupported format of svodEndDate '{}' in recent film: {}, expected '%Y-%m-%d %H:%M'".
                        format(svod_end_date, title)) from None

    end_date = content.get('endDate')
    if end_date:
        try:
            end_time = time.strptime(end_date, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                end_time = time.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise AssertionError(
                    "Unexpected format of endDate '{}' in {}, expected '%Y-%m-%d %H:%M'".format(end_date, title)
                ) from None
        if end_time > time.gmtime():
            print(" NOTE: End date of '{}' is in the future: {}".format(title, time.asctime(end_time)))

    prod_year = content.get('productionYear')
    if prod_year:
        # assert productionYear is a 4 digit integer.
        assert prod_year.isdecimal(), \
            "Expected numeric string for productionYear in {}, got {}".format(title, prod_year)
        assert int(prod_year) > 1800, "Invalid value for {}: {}, expect value > 1800.".format(
            title + '.content.productionYear', prod_year)

    duration = content.get('duration')
    # The duration field can be absent, empty, None, a sting in the format '104 min', or
    # a string with just a number, that even can be either a float or an int. If present,
    # the value is always the duration in minutes.
    if duration:
        d = duration.split()
        try:
            float(d[0])
            assert 0 < len(d) < 3
            if len(d) == 2:
                assert d[1] == 'min'
        except (ValueError, AssertionError):
            raise AssertionError(
                "Unexpected format for {}: '{}', expect like '3.45', '104', or '104 min'.".format(
                    title + '.duration', duration)
            ) from None

    price = content.get('tvodPrice')
    if price:
        # tvodPrice can be an empty string, a string with a number that may be '0', or an int.
        price = int(price)
        if price:
            assert 100 < price < 800, "Unexpected value '{}' of '{}'".format(price, title + '.tvodPrice')

    subscribers_price = content.get('tvodSubscribersPrice')
    if subscribers_price:
        # tvodSubscribersPrice can be an empty string, a string with a number that may be '0', or an int.
        subscribers_price = int(subscribers_price)
        if subscribers_price:
            assert 90 < int(subscribers_price) < 700, "Unexpected value '{}' of '{}'".format(
                price, title + '.tvodSubscribersPrice')


def check_films_data_list(films_list, additional_content_keys=None, allow_none_values=True):
    """Check all items in a list of film info, as obtained from Cinetree."""
    assert isinstance(films_list, list), "Films list is not of type List, but {}".format(type(films_list))
    for film_info in films_list:
        # Depending on the origin of the list, some items in some film lists can be None
        if film_info is not None:
            check_film_data(film_info, additional_content_keys)
        elif not allow_none_values:
            raise AssertionError("Unexpected None value in a list of films.")


def check_rentals(rentals_obj):
    """Check the object that is returns from the js document retrieved at
    the page 'huurfilms', or it's equivalent at storyblok.

    """
    has_keys(rentals_obj, 'featured', 'collections', 'filterGenre', 'filterCountry', 'filterDuration',
             'filterGenreItems', 'filterDurationItems', obj_name='rentals_object')
    num_coll = len(rentals_obj['collections'])
    # Rentals does not return all collection, but only e preferred selection.
    assert 4 < num_coll < 8, "Unexpected number of collection, expected 5, got {}".format(num_coll)
    genres = set(rentals_obj['filterGenreItems'].split(','))
    assert genres == set(ct_api.GENRES), "Genres have changed"
    durations = rentals_obj['filterDurationItems']
    assert len(durations) == 3, "Number of duration filter changed from 3 to {}".format(len(durations))
    assert durations[0]['from'] == '0' and durations[0]['to'] == '59', \
        "Duration filter[0] has changed: {}".format(durations[0])
    assert durations[1]['from'] == '60' and durations[1]['to'] == '120', \
        "Duration filter[1] has changed: {}".format(durations[1])
    assert durations[2]['from'] == '121' and durations[2]['to'] == '500', \
        "Duration filter[2] has changed: {}".format(durations[2])


def check_collection(test, col):
    """Check a collection object

    """
    test.assertIsInstance(col, dict)
    test.assertTrue('label' in col.keys())
    test.assertTrue('art' in col.keys())
    test.assertTrue('info' in col.keys())
    test.assertTrue('slug' in col['params'].keys())
