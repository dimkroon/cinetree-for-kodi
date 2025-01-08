
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import json
import time

from tests.support import fixtures
fixtures.global_setup()

import unittest
from unittest.mock import patch, mock_open

from resources.lib import errors
from resources.lib.ctree import ct_account

# noinspection PyPep8Naming
setUpModule = fixtures.setup_local_tests
tearDownModule = fixtures.tear_down_local_tests


account_data = {"uname": "my_uname", "refreshed": time.time(),
                "login_session": {"user": {"_id": "2e8e4ca4a7806900bd15d8e5", "email": "mail@domain.com",
                                           "name": {"first": "My", "last": "Name"}, "displayName": "My Full Name",
                                           "lastLogin": "2022-05-14T20:59:56.163Z"
                                           },
                                  "token": "my-token",
                                  "refreshToken": "my-refresh-token"
                                  }
                }


class TestSession(unittest.TestCase):
    def test_instantiate_account_class(self):
        cinetree_sess = ct_account.Session()
        assert cinetree_sess is not None

    def test_session(self):
        ct_account._session_obj = None
        cinetree_sess = ct_account.session()
        self.assertIsInstance(cinetree_sess, ct_account.Session)


@patch("resources.lib.ctree.ct_account.Session.save_account_data")
class TestLogin(unittest.TestCase):
    @patch("resources.lib.kodi_utils.ask_credentials", return_value=('your_name', 'your_passw'))
    @patch('resources.lib.fetch.post_json', return_value={'key': 'value'})
    def test_login(self, p_post, p_ask, patched_save):
        ct_sess = ct_account.Session()
        self.assertTrue(ct_sess.login())
        self.assertEqual(p_post.call_args[0][1], {'username': 'your_name', 'password': 'your_passw'})
        patched_save.assert_called_once()
        p_ask.assert_called_once()
        self.assertEqual(ct_sess.account_data['login_session'], {'key': 'value'})

    @patch("resources.lib.kodi_utils.ask_credentials", return_value=('your_name', 'your_passw'))
    @patch('resources.lib.fetch.post_json')
    def test_login_with_credentials(self, p_post, p_ask, _):
        """Credentials passed are used as default values for the on-screenkeyboard ask_credentials
        will show. Ask_credentials() will return the user input."""
        ct_sess = ct_account.Session()
        ct_sess.uname = 'your_name'
        ct_sess.passw = 'your_passw'
        self.assertTrue(ct_sess.login('my_name', 'my_passw'))
        p_ask.assert_called_once_with('my_name', 'my_passw')
        self.assertEqual(p_post.call_args[0][1], {'username': 'your_name', 'password': 'your_passw'})

    @patch("resources.lib.kodi_utils.ask_credentials", side_effect=[('', ''), ('my_name', ''), ('', 'my_passw')])
    @patch('resources.lib.fetch.post_json')
    def test_user_cancels_entry(self, p_post, _, __):
        """Test all situation where NOT both username and password are provided.
        The last one should practically never occur though."""
        for _ in range(3):
            ct_sess = ct_account.Session()
            self.assertFalse(ct_sess.login())
        p_post.assert_not_called()

    @patch("resources.lib.kodi_utils.ask_credentials", return_value=('my_name', 'my_password'))
    @patch("resources.lib.kodi_utils.ask_login_retry", return_value=False)
    def test_login_encounters_http_errors_without_retry(self, p_ask_retry, p_ask_cred, p_save):
        with patch('resources.lib.fetch.post_json', side_effect=errors.AuthenticationError):
            ct_sess = ct_account.Session()
            self.assertRaises(errors.AuthenticationError, ct_sess.login,)
            p_ask_retry.assert_called_once()
            p_ask_cred.assert_called_once()
            p_save.assert_not_called()

            p_ask_retry.reset_mock()
            p_ask_cred.reset_mock()
        with patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(400, '')):
            ct_sess = ct_account.Session()
            self.assertRaises(errors.HttpError, ct_sess.login)
            p_ask_retry.assert_not_called()
            p_ask_cred.assert_called_once()
            p_save.assert_not_called()

            p_ask_cred.reset_mock()
        with patch('resources.lib.fetch.post_json', side_effect=errors.GeoRestrictedError):
            ct_sess = ct_account.Session()
            self.assertRaises(errors.GeoRestrictedError, ct_sess.login)
            p_ask_retry.assert_not_called()
            p_ask_cred.assert_called_once()
            p_save.assert_not_called()


@patch("resources.lib.kodi_utils.ask_login_retry", side_effect=(True, False))
@patch("resources.lib.ctree.ct_account.Session.save_account_data", new=lambda _: True)
class LoginRetryBehaviour(unittest.TestCase):
    @patch('resources.lib.fetch.post_json', return_value={'key': 'value'})
    @patch("resources.lib.kodi_utils.ask_credentials", new=lambda a, b: ('my_name', 'my_password'))
    def test_login_no_retry_on_sucessfull_login(self, _,  p_ask_retry):
        ct_sess = ct_account.Session()
        ct_sess.login()
        p_ask_retry.assert_not_called()

    @patch('resources.lib.fetch.post_json', side_effect=errors.AuthenticationError)
    @patch("resources.lib.kodi_utils.ask_credentials", new=lambda a, b: ('', ''))
    def test_login_no_retry_on_canceled_credentials(self, _, p_ask_retry):
        ct_sess = ct_account.Session()
        self.assertFalse(ct_sess.login())
        p_ask_retry.assert_not_called()

    @patch('resources.lib.fetch.post_json', side_effect=errors.AuthenticationError)
    @patch("resources.lib.kodi_utils.ask_credentials", side_effect=(('my_name', 'my_password'), ('', '')))
    def test_login_no_second_retry_on_canceled_credentials(self, _, __, p_ask_retry):
        """The user cancels entering credentials after the first retry has been offered"""
        ct_sess = ct_account.Session()
        self.assertFalse(ct_sess.login())
        p_ask_retry.assert_called_once()

    @patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(400, ''))
    @patch("resources.lib.kodi_utils.ask_credentials", new=lambda a, b: ('my_name', 'my_password'))
    def test_login_no_retry_on_other_errors(self, _, p_ask_retry):
        """A retry should only be offered on AuthenticationErrors"""
        ct_sess = ct_account.Session()
        self.assertRaises(errors.HttpError, ct_sess.login)
        p_ask_retry.assert_not_called()

    @patch('resources.lib.fetch.post_json', side_effect=errors.AuthenticationError)
    @patch("resources.lib.kodi_utils.ask_credentials", new=lambda a, b: ('my_name', 'my_password'))
    def test_login_retry_on_wrong_credentials(self, p_post, p_ask_retry):
        ct_sess = ct_account.Session()
        self.assertRaises(errors.AuthenticationError, ct_sess.login)
        self.assertEqual(2, p_ask_retry.call_count)
        self.assertEqual(2, p_post.call_count)      # 1 original login, 1 after first retry



@patch("resources.lib.ctree.ct_account.Session.save_account_data")
class Refresh(unittest.TestCase):
    def setUp(self) -> None:
        self.ct_sess = ct_account.Session()
        self.ct_sess.account_data = {'login_session': {'token': '1st_token', 'refreshToken': '1st_refresh'}}

    @patch('resources.lib.fetch.post_json', return_value={'token': '2nd_token', 'refreshToken': '2nd_refresh'})
    def test_refresh(self, _, p_save):
        self.assertTrue(self.ct_sess.refresh())
        self.assertTrue(p_save.called_once())
        self.assertEqual(self.ct_sess.account_data['login_session'], {'token': '2nd_token', 'refreshToken': '2nd_refresh'})

    def test_refresh_with_http_errors(self, p_save):
        with patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(400, 'Bad request')):
            self.assertFalse(self.ct_sess.refresh())
        with patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(401, 'Unauthorized')):
            self.assertFalse(self.ct_sess.refresh())
        with patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(403, 'Forbidden')):
            self.assertFalse(self.ct_sess.refresh())
        with patch('resources.lib.fetch.post_json', side_effect=errors.HttpError(404, 'Not found')):
            self.assertFalse(self.ct_sess.refresh())
        p_save.assert_not_called()

    @patch('resources.lib.fetch.post_json', return_value={'token': '2nd_token', 'refreshToken': '2nd_refresh'})
    def test_refresh_without_account_data(self, p_post, p_save):
        ct_sess = ct_account.Session()
        ct_sess.account_data = None
        self.assertFalse(ct_sess.refresh())
        p_post.assert_not_called()
        p_save.assert_not_called()


class PropAccessToken(unittest.TestCase):
    @patch('resources.lib.ctree.ct_account.Session.login')
    @patch('resources.lib.ctree.ct_account.Session.refresh')
    def test_prop_access_token(self, p_refresh, p_login):
        ct_sess = ct_account.Session()
        ct_sess.account_data = account_data
        self.assertEqual(account_data['login_session']['token'], ct_sess.access_token)
        p_refresh.assert_not_called()
        p_login.assert_not_called()

    @patch('resources.lib.ctree.ct_account.Session.login')
    @patch('resources.lib.ctree.ct_account.Session.refresh', return_value=True)
    def test_prop_access_token_raises_auth_error_on_no_account_data(self, p_refresh, p_login):
        ct_sess = ct_account.Session()
        ct_sess.account_data = None
        with self.assertRaises(errors.AuthenticationError):
            # noinspection PyStatementEffect
            ct_sess.access_token    # TypeError as mocked login does not update account_data
        p_login.assert_not_called()
        p_refresh.assert_not_called()

    @patch('resources.lib.ctree.ct_account.Session.login')
    @patch('resources.lib.ctree.ct_account.Session.refresh', return_value=True)
    def test_prop_access_token_with_cache_timed_out_invokes_refresh(self, p_refresh, p_login):
        ct_sess = ct_account.Session()
        ct_sess.account_data = account_data
        ct_sess.account_data['refreshed'] = time.time() - 13 * 3600     # force a timeout
        # noinspection PyStatementEffect
        ct_sess.access_token
        p_login.assert_not_called()
        p_refresh.assert_called_once()


class Misc(unittest.TestCase):
    def test_read_account_data(self):
        with patch('resources.lib.ctree.ct_account.open', mock_open(read_data=json.dumps(account_data))):
            # test data is being read an class instantiation
            ct_sess = ct_account.Session()
            self.assertEqual(account_data, ct_sess.account_data)
            ct_sess.account_data = None
            # test manual read
            ct_sess.read_account_data()
            self.assertEqual(account_data, ct_sess.account_data)
        with patch('resources.lib.ctree.ct_account.open', side_effect=OSError):
            ct_sess.read_account_data()
            self.assertEqual({}, ct_sess.account_data)

    @patch("resources.lib.ctree.ct_account.open")
    def test_save_account_data(self, p_open):
        ct_sess = ct_account.session()
        ct_sess.save_account_data()
        p_open.assert_called_once()
        self.assertGreater(len(p_open.mock_calls), 2)   # at least calls to __enter__, write , __exit__

    @patch("resources.lib.ctree.ct_account.Session.save_account_data")
    def test_logout(self, p_save):
        ct_sess = ct_account.session()
        ct_sess.account_data = {"some data"}
        ct_sess.log_out()
        self.assertEqual(ct_sess.account_data, {})
        p_save.assert_called_once()
