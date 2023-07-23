
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from __future__ import annotations
import os

from unittest.mock import patch


patch_g = None


def global_setup():
    """Fixture required for all test.
    Ensure this is imported and called in every test module first thing. At least before
    importing any other module from the project or other kodi related module.

    As it is global for all tests there is no need to tear down.
    """
    # Ensure that kodi's special://profile refers to a predefined folder. Just in case
    # some code want to write, whether intentional or not.
    global patch_g
    if patch_g is None:
        profile_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'addon_profile_dir'))
        patch_g = patch('xbmcaddon.Addon.getAddonInfo', new=lambda self, item: profile_dir if item == 'profile' else '')
        patch_g.start()

        # Use an xbmcgui.ListItem that stores the values which have been set.
        patch_listitem()


patch_1 = None


class RealWebRequestMadeError(Exception):
    pass


def setup_local_tests():
    """Module level fixture for all local tests. Ensures that no unintentional real
    web requests can occur.

    """
    global patch_1
    patch_1 = patch('requests.sessions.Session.send', side_effect=RealWebRequestMadeError)
    patch_1.start()


def tear_down_local_tests():
    global patch_1
    if patch_1:
        patch_1.stop()
        patch_1 = None


def setup_web_test(*args):
    try:
        from tests import account_login
        account_login.set_credentials()
    except ImportError:
        pass


def patch_listitem():
    import xbmcgui

    class LI(xbmcgui.ListItem):
        def __init__(self, label: str = "",
                     label2: str = "",
                     path: str = "",
                     offscreen: bool = False) -> None:
            super().__init__()
            assert isinstance(label, str)
            assert isinstance(label2, str)
            assert isinstance(path, str)
            assert isinstance(offscreen, bool)
            self._label = label
            self._label2 = label2
            self._path = path
            self._offscreen = offscreen
            self._is_folder = False
            self._art = {}
            self._info = {}
            self._props = {}

        def getLabel(self) -> str:
            return self._label

        def getLabel2(self) -> str:
            return self._label2

        def setLabel(self, label: str) -> None:
            assert isinstance(label, str), "Argument 'label' must be a string."
            self._label = label

        def setLabel2(self, label: str) -> None:
            assert isinstance(label, str), "Argument 'label' must be a string."
            self._label2 = label

        def setArt(self, dictionary: dict[str, str]) -> None:
            assert isinstance(dictionary, dict), "Argument 'dictionary' must be a dict."
            self._art.update(dictionary)

        def setIsFolder(self, isFolder: bool) -> None:
            assert isinstance(isFolder, bool), "Argument 'isFolder' must be a boolean."
            self._is_folder = isFolder

        def setInfo(self, type: str, infoLabels: dict[str, str]) -> None:
            assert isinstance(type, str), "Argument 'type' must be a string."
            assert isinstance(infoLabels, dict), "Argument 'infoLabels' must be a dict."
            assert type in ('video', 'music', 'pictures', 'game')
            info_dict = self._info.setdefault(type, {})
            info_dict.update(infoLabels)

        def setProperty(self, key: str, value: str) -> None:
            assert isinstance(key, str), "Argument 'key' must be a string."
            assert isinstance(value, str), "Argument 'value' must be a string."
            self._props[key] = value

        def setProperties(self, dictionary: dict[str, str]) -> None:
            assert isinstance(dictionary, dict), "Argument 'dictionary' must be a dict."
            self._props.update(dictionary)

        def getProperty(self, key: str) -> str:
            assert isinstance(key, str), "Argument 'key' must be a string."
            return self._props['key']

        def setPath(self, path: str) -> None:
            assert isinstance(path, str), "Argument 'path' must be a string."
            self._path = path

        def setMimeType(self, mimetype: str) -> None:
            assert isinstance(mimetype, str), "Argument 'mimetype' must be a string."
            self._mimetype = mimetype

        def setContentLookup(self, enable: bool) -> None:
            assert isinstance(enable, bool), "Argument 'enable' must be a boolean."
            self._content_lookup = enable

        def setSubtitles(self, subtitleFiles: dict[str]) -> None:
            assert isinstance(subtitleFiles, (list, tuple)), "Argument 'subtitleFiles' must be a tuple or a list."
            self._subtitles = subtitleFiles

        def getPath(self) -> str:
            return self._path

    xbmcgui.ListItem = LI