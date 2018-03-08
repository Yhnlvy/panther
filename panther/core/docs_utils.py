# -*- coding:utf-8 -*-
#
# Copyright 2016 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

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
