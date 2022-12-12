
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import json
import os.path
import re

from requests.models import Response

from resources.lib import jsonp


def doc_path(doc: str) -> str:
    """Return the full path to doc in the directory test_docs.
    Makes test docs accessible independent of the current working dir while
    avoiding the use absolute paths.

    .. note ::
        The directory test_docs is to a sibling of this module's parent directory

    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), '../test_docs', doc))


def open_jsonp(filename: str):
    full_path = doc_path(filename)
    with open(full_path) as f:
        jsonp_doc = f.read()
    data = jsonp.parse(jsonp_doc)
    return data


def open_json(filename):
    full_path = doc_path(filename)
    with open(full_path) as f:
        return json.load(f)


def is_uuid(uuid: str) -> bool:
    """Test if *uuid* is indeed a uuid"""
    return re.match(r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$', uuid) is not None


def open_doc(doc):
    """Returns a partial object that accepts any set of arguments and returns
    the contents of the file specified by *doc_path*.

    Intended to be used as new object in patched tests. In particular to return
    locally saved documents instead of doing web requests.

    """
    def wrapper(*args, **kwargs):
        with open(doc_path(doc), 'r') as f:
            return f.read()
    return wrapper


def save_json(data, filename):
    """Save a data structure in json format to a file in the test_docs directory"""
    with open(doc_path(filename), 'w') as f:
        json.dump(data, f)


def save_doc(data, filename):
    """Save a data as text to a file in the test_docs directory"""
    with open(doc_path(filename), 'w') as f:
        f.write(data)


class HttpResponse(Response):
    """Create a requests.Response object with various attributes set.
    Can be used as the `return_value` of a mocked request.request.

    """
    def __init__(self, status_code: int = None, headers: dict = None, content: bytes = None, reason=None):
        super().__init__()
        if status_code is not None:
            self.status_code = status_code
        if headers is not None:
            for k, v in headers.items():
                self.headers[k] = v
        if reason is not None:
            self.reason = reason
        if content is not None:
            self._content = content
            if status_code is None:
                self.status_code = 200
                self.reason = 'OK'


def get_sb_film(uuid=None, genre=None, page=None, items_per_page=None):
    """Return a list of films from a stored dump of storyblok films

    :param uuid: a single uuid as string or an iterable of uuids
    :param genre: a case-insensitive string of genre

    """
    films = open_json('st_blok/films.json')

    if uuid:
        if isinstance(uuid, str):
            film = films.get(uuid)
            result = [film] if film else []
        else:
            result = [v for k,v in films.items() if k in uuid]
    elif genre:
        genre = genre.lower()
        result = [v for v in films.values() if genre in v['content'].get('genre', '').lower()]
    else:
        result = []
        # raise ValueError("Missing arguments. At least one argument must be supplied.")

    if items_per_page and page:
        start = items_per_page * (page - 1) if page else 0
        end = start + items_per_page
        return result[start:end], len(result)
    else:
        return result, len(result)
