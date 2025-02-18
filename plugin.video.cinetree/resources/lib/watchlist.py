# ------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------
import os
import logging
import pickle
from datetime import datetime
from collections.abc import MutableMapping

import xbmc
from codequick import Route, Script, Listitem
from codequick.support import logger_id

from resources.lib import utils
from resources.lib.ctree.ct_data import FilmItem


logger = logging.getLogger('.'.join((logger_id, __name__)))

TXT_ADD_TO_WATCHLIST = Script.localize(30860)
TXT_REMOVE_FROM_WATCHLIST = Script.localize(30861)


class WatchList(MutableMapping):
    def __init__(self):
        self._fname = 'watchlist'
        self._path = os.path.join(utils.addon_info['profile'], self._fname)
        self._data = {}
        self.__has_changed = False
        self._data = self._read()

    def _read(self):
        try:
            with open(self._path, 'rb') as f:
                data = pickle.load(f)
                logger.debug("WatchList loaded. Data = %s", data)
                return data
        except FileNotFoundError:
            logger.debug("WatchList file not found.")
        except (pickle.UnpicklingError, EOFError) as err:
            logger.error("Failed to read from file: %r", err)
        return {}

    def save(self):
        logger.debug("Saving watch list...")
        with open(self._path, 'wb') as f:
            pickle.dump(self._data, f)
        self.__has_changed = False

    def append(self, film_uid: str, title: str) -> bool:
        """Save a new film to the Watch List.

        Save the title as well; if the film ever becomes unavailable on cinetree,
        it's still possible to inform the user about it with the title of the film.
        """
        if not film_uid:
            return False
        if film_uid in self._data:
            logger.error("Cannot append, film '%s': '%s' is already on the Watch List.", film_uid, title)
            return False

        self._data[film_uid] = {
            'added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title': title}
        self.__has_changed = True
        logger.info("Film '%s': '%s' added to the Watch List.", film_uid, title)
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__has_changed:
            self.save()

    def __contains__(self, item):
        return item in self._data

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()

    def __delitem__(self, film_uid):
        title = self._data[film_uid].get('title')
        del self._data[film_uid]
        logger.info("Film %s: '%s' removed from Watch List.", film_uid, title)
        self.__has_changed = True

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, value):
        raise NotImplementedError

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()


@Script.register()
def edit(_, film_uuid, title, action):
    with WatchList() as wl:
        if action == 'add':
            wl.append(film_uuid, title)
        elif action == 'remove':
            del wl[film_uuid]
    xbmc.executebuiltin('Container.Refresh')


def create_ctx_mnu(li: Listitem, film: FilmItem, wl: WatchList):
    """Add an 'add/remove to My List' context menu item to the Listitem"""
    is_on_watchlist = film.uuid in wl
    li.context.script(edit,
                      TXT_REMOVE_FROM_WATCHLIST if is_on_watchlist else TXT_ADD_TO_WATCHLIST,
                      film_uuid=film.uuid,
                      title=film.data['info']['title'],
                      action='remove' if is_on_watchlist else 'add')
