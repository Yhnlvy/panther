# -*- coding:utf-8 -*-

# where our docs are hosted
BASE_URL = 'https://docs.openstack.org/panther/latest/'


def get_url(bid):
    # NOTE(tkelsey): for some reason this import can't be found when stevedore
    # loads up the formatter plugin that imports this file. It is available
    # later though.
    from panther.core import extension_loader

    info = extension_loader.MANAGER.plugins_by_id.get(bid)
    if info is not None:
        return BASE_URL + ('plugins/%s.html' % info.plugin.__name__)

    return BASE_URL  # no idea, give the docs main page
