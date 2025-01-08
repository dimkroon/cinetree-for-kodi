
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import sys
import os

from tests.support.fixtures import global_setup
global_setup()


from codequick import Route, Listitem, Script, run

call_count = 0


@Route.register(cache_ttl=60)
def caching_callback(_):
    global call_count
    call_count += 1
    return (Listitem(content_type='movie'), )


def patch_cc_route():
    original_call = Route.__call__

    def patched_call(self, route, args, kwargs):
        self.__dict__.update(route.parameters)
        original_call(self, route, args, kwargs)

    Route.__call__ = patched_call


if __name__ == '__main__':
    try:
        os.remove(os.path.join(Script.get_info('profile'), 'listitem_cache.sqlite'))
    except OSError:
        pass
    sys.argv = ("/main/caching_callback/", '10', '')

    run()
    run()
    run()
    assert call_count == 3, \
        'Caching works without patch; callback has been called {} times, expected 3'.format(call_count)

    call_count = 0
    patch_cc_route()
    run()
    run()
    run()
    assert call_count == 1, \
        'Callback has been called {} times, expected 1'.format(call_count)
