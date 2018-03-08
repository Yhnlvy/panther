# -*- coding:utf-8 -*-
#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
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


import importlib
import logging


from panther.core import extension_loader


LOG = logging.getLogger(__name__)


class PantherTestSet(object):
    def __init__(self, config, profile=None):
        if not profile:
            profile = {}
        extman = extension_loader.MANAGER
        filtering = self._get_filter(config, profile)
        self.plugins = [p for p in extman.plugins
                        if p.plugin._test_id in filtering]
        self._load_tests(config, self.plugins)

    @staticmethod
    def _get_filter(config, profile):
        extman = extension_loader.MANAGER

        inc = set(profile.get('include', []))
        exc = set(profile.get('exclude', []))

        if inc:
            filtered = inc
        else:
            filtered = set(extman.plugins_by_id.keys())
        return filtered - exc


    def _load_tests(self, config, plugins):
        '''Builds a dict mapping tests to node types.'''
        self.tests = {}
        for plugin in plugins:
            if hasattr(plugin.plugin, '_takes_config'):
                # TODO(??): config could come from profile ...
                cfg = config.get_option(plugin.plugin._takes_config)
                if cfg is None:
                    genner = importlib.import_module(plugin.plugin.__module__)
                    cfg = genner.gen_config(plugin.plugin._takes_config)
                plugin.plugin._config = cfg
            for check in plugin.plugin._checks:
                self.tests.setdefault(check, []).append(plugin.plugin)
                LOG.debug('added function %s (%s) targeting %s',
                          plugin.name, plugin.plugin._test_id, check)

    def get_tests(self, checktype):
        '''Returns all tests that are of type checktype

        :param checktype: The type of test to filter on
        :return: A list of tests which are of the specified type
        '''
        return self.tests.get(checktype) or []
