# ------------------------------------------------------------------------------
#  Copyright (c) 2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

from tests.support import fixtures
fixtures.global_setup()

import os
import pickle

from unittest import TestCase
from unittest.mock import patch, mock_open, call

from codequick import Listitem
from resources.lib import utils
from resources.lib import watchlist
from resources.lib.ctree.ct_data import FilmItem

setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


class TestWatchlist(TestCase):
    def setUp(self):
        try:
            os.unlink(os.path.join(utils.addon_info['profile'], 'watchlist'))
        except FileNotFoundError:
            pass

    def tearDown(self):
        self.setUp()

    def test_watchlist_read(self):
        with patch("builtins.open", mock_open(
                read_data=pickle.dumps({'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"}}))):
            data = watchlist.WatchList()._read()
            self.assertDictEqual(data, {'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"}})
        # Missing file
        with patch("builtins.open", side_effect=FileNotFoundError):
            data = watchlist.WatchList()._read()
            self.assertDictEqual({}, data)
        # Empty file
        with patch("builtins.open", mock_open(read_data=b'')):
            data = watchlist.WatchList()._read()
            self.assertEqual({}, data)
        # Invalid file data
        with patch("builtins.open", mock_open(read_data=b'15fcjksl085')):
            data = watchlist.WatchList()._read()
            self.assertEqual({}, data)

    @patch("resources.lib.watchlist.WatchList._read", return_value={
        'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"},
        'efgh': {'added': '2023-02-02 03:04:05', 'title': "other film"}})
    def test_watchlist_data(self, p_read):
        wl = watchlist.WatchList()
        p_read.assert_called_once()
        self.assertEqual(2, len(wl))
        self.assertDictEqual(wl['abcd'], {'added': '2022-01-01 00:01:02', 'title': "a film"})
        with self.assertRaises(NotImplementedError):
            wl['abcd'] = {'added': '2024-03-03 06:07:08', 'title': "no film"}
        self.assertTrue('efgh' in wl)
        self.assertListEqual(['abcd', 'efgh'], list(wl.keys()))
        self.assertListEqual(
            [{'added': '2022-01-01 00:01:02', 'title': "a film"},
             {'added': '2023-02-02 03:04:05', 'title': "other film"}],
            list(wl.values()))
        self.assertListEqual(
            [('abcd', {'added': '2022-01-01 00:01:02', 'title': "a film"}),
             ('efgh', {'added': '2023-02-02 03:04:05', 'title': "other film"})],
            list(wl.items()))

    @patch("resources.lib.watchlist.WatchList._read", return_value={
        'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"}})
    def test_append(self, _):
        wl = watchlist.WatchList()
        self.assertEqual(1, len(wl))
        result = wl.append('efgh', 'other film')
        self.assertIs(result, True)
        self.assertEqual(2, len(wl))
        # append an already existing item
        result = wl.append('efgh', 'other film')
        self.assertIs(result, False)
        # noinspection PyTypeChecker
        result = wl.append(None, 'other film')
        self.assertIs(result, False)
        result = wl.append('', 'other film')
        self.assertIs(result, False)
        self.assertEqual(2, len(wl))

    @patch("resources.lib.watchlist.WatchList._read", return_value={
        'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"},
        'efgh': {'added': '2023-02-02 03:04:05', 'title': "other film"}})
    def test_delete(self, _):
        wl = watchlist.WatchList()
        self.assertEqual(2, len(wl))
        del wl['abcd']
        self.assertEqual(1, len(wl))
        with self.assertRaises(KeyError):
            _ = wl['abcd']
        # Remove a non-existing item
        with self.assertRaises(KeyError):
            del wl['xyz']

    @patch("resources.lib.watchlist.WatchList._read", return_value={})
    def test_save(self, _):
        wl = watchlist.WatchList()
        with patch("builtins.open", mock_open()) as p_open:
            wl.append('id1', 'film1')
            wl.save()
        p_open.assert_called_once()
        self.assertTrue('wb' in p_open.call_args.args)

    @patch("resources.lib.watchlist.WatchList._read", return_value={})
    def test_context_manager(self, p_read):
        with patch("resources.lib.watchlist.WatchList.save") as p_save:
            with watchlist.WatchList() as wl:
                wl.append('id1', 'film1')
            p_read.assert_called_once()
            p_save.assert_called_once()
        # Save only when something has changed.
        with patch("resources.lib.watchlist.WatchList.save") as p_save:
            with watchlist.WatchList():
                pass
            self.assertEqual(2, p_read.call_count)
            p_save.assert_not_called()


# noinspection PyMethodMayBeStatic
@patch('resources.lib.watchlist.WatchList')
class Edit(TestCase):
    def test_edit_add(self, p_watchlist):
        watchlist.edit.test('uid1', 'a film', 'add')
        p_watchlist.has_call(
            call().__enter().append('uid1', 'a film')
        )

    def test_edit_remove(self, p_watchlist):
        watchlist.edit.test('uid1', 'a film', 'remove')
        p_watchlist.has_call(
            call().__enter().__delitem__('uid1')
        )


@patch("resources.lib.watchlist.WatchList._read", return_value={
        'abcd': {'added': '2022-01-01 00:01:02', 'title': "a film"}})
@patch("resources.lib.watchlist.TXT_ADD_TO_WATCHLIST", 'Add')
@patch("resources.lib.watchlist.TXT_REMOVE_FROM_WATCHLIST", 'Remove')
class CreateContextMEnu(TestCase):
    def test_item_exists(self, _):
        li = Listitem()
        fi = FilmItem({'uuid': 'abcd', 'content': {'title': 'a film', 'endDate': '2050-01-01 00:00'}})
        watchlist.create_ctx_mnu(li, fi, watchlist.WatchList())
        self.assertEqual('Remove', li.context[0][0])

    def test_item_not_exists(self, _):
        li = Listitem()
        fi = FilmItem({'uuid': 'efgh', 'content': {'title': 'a film', 'endDate': '2050-01-01 00:00'}})
        watchlist.create_ctx_mnu(li, fi, watchlist.WatchList())
        self.assertEqual('Add', li.context[0][0])
