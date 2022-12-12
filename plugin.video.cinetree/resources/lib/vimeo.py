
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import xbmcgui

from .fetch import get_json


def get_steam_url(video_url, max_resolution=None):
    """Return a direct url to a stream of the specified video.

    Cinetree returns a trailer url like "https://vimeo.com/334256156"
    The config, however, is obtained from https://player.vimeo.com/video

    """
    if video_url.endswith('/'):
        video_url = video_url[:-1]

    video_id = video_url.split('/')[-1]
    config_url = ''.join(('https://player.vimeo.com/video/', video_id, '/config'))
    config = get_json(config_url)
    stream_config = config['request']['files']['progressive']

    max_video_height = get_height(max_resolution)
    best_match = {}
    matched_h = 0

    for stream in stream_config:
        h = stream['height']
        if matched_h < h <= max_video_height:
            best_match = stream
            matched_h = h

    return best_match.get('url', '')


def get_height(resolution):
    if resolution is None:
        return xbmcgui.getScreenHeight() or 9999
    if isinstance(resolution, (str, bytes)):
        resolution = resolution.split('x', 1)[-1]
    return int(resolution)
