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

import logging

import yaml

from panther.core import constants
from panther.core import extension_loader
from panther.core import utils


LOG = logging.getLogger(__name__)


class PantherConfig(object):
    def __init__(self, config_file=None):
        '''Attempt to initialize a config dictionary from a yaml file.

        Error out if loading the yaml file fails for any reason.
        :param config_file: The Panther yaml config file

        :raises panther.utils.ConfigError: If the config is invalid or
            unreadable.
        '''
        self.config_file = config_file
        self._config = {}

        if config_file:
            try:
                f = open(config_file, 'r')
            except IOError:
                raise utils.ConfigError("Could not read config file.",
                                        config_file)

            try:
                self._config = yaml.safe_load(f)
                self.validate(config_file)
            except yaml.YAMLError as err:
                LOG.error(err)
                raise utils.ConfigError("Error parsing file.", config_file)

            # valid config must be a dict
            if not isinstance(self._config, dict):
                raise utils.ConfigError("Error parsing file.", config_file)

            self.convert_legacy_config()

        else:
            # use sane defaults
            self._config['plugin_name_pattern'] = '*.py'
            self._config['include'] = ['*.js']

        self._init_settings()

    def get_option(self, option_string):
        '''Returns the option from the config specified by the option_string.

        '.' can be used to denote levels, for example to retrieve the options
        from the 'a' profile you can use 'profiles.a'
        :param option_string: The string specifying the option to retrieve
        :return: The object specified by the option_string, or None if it can't
        be found.
        '''
        option_levels = option_string.split('.')
        cur_item = self._config
        for level in option_levels:
            if cur_item and (level in cur_item):
                cur_item = cur_item[level]
            else:
                return None

        return cur_item

    def get_setting(self, setting_name):
        if setting_name in self._settings:
            return self._settings[setting_name]
        else:
            return None

    @property
    def config(self):
        '''Property to return the config dictionary

        :return: Config dictionary
        '''
        return self._config

    def _init_settings(self):
        '''This function calls a set of other functions (one per setting)

        This function calls a set of other functions (one per setting) to build
        out the _settings dictionary.  Each other function will set values from
        the config (if set), otherwise use defaults (from constants if
        possible).
        :return: -
        '''
        self._settings = {}
        self._init_plugin_name_pattern()

    def _init_plugin_name_pattern(self):
        '''Sets settings['plugin_name_pattern'] from default or config file.'''
        plugin_name_pattern = constants.plugin_name_pattern
        if self.get_option('plugin_name_pattern'):
            plugin_name_pattern = self.get_option('plugin_name_pattern')
        self._settings['plugin_name_pattern'] = plugin_name_pattern
    
    def convert_legacy_config(self):
        updated_profiles = self.convert_names_to_ids()

        if updated_profiles:
            self._config['profiles'] = updated_profiles

    def convert_names_to_ids(self):
        '''Convert test names to IDs, unknown names are left unchanged.'''
        extman = extension_loader.MANAGER

        updated_profiles = {}
        for name, profile in (self.get_option('profiles') or {}).items():
            # NOTE(tkelsey): can't use default of get() because value is
            # sometimes explicity 'None', for example when the list if given in
            # yaml but not populated with any values.
            include = set((extman.get_plugin_id(i) or i)
                          for i in (profile.get('include') or []))
            exclude = set((extman.get_plugin_id(i) or i)
                          for i in (profile.get('exclude') or []))
            updated_profiles[name] = {'include': include, 'exclude': exclude}
        return updated_profiles
    
    def validate(self, path):
        '''Validate the config data.'''
        legacy = False
        message = ("Config file has an include or exclude reference "
                   "to legacy test '{0}' but no configuration data for "
                   "it. Configuration data is required for this test. "
                   "Please consider switching to the new config file "
                   "format, the tool 'panther-config-generator' can help "
                   "you with this.")

        def _test(key, block, exclude, include):
            if key in exclude or key in include:
                if self._config.get(block) is None:
                    raise utils.ConfigError(message.format(key), path)

        if 'profiles' in self._config:
            legacy = True
            for profile in self._config['profiles'].values():
                inc = profile.get('include') or set()
                exc = profile.get('exclude') or set()

        # show deprecation message
        if legacy:
            LOG.warning("Config file '%s' contains deprecated legacy config "
                        "data. Please consider upgrading to the new config "
                        "format. The tool 'panther-config-generator' can help "
                        "you with this. Support for legacy configs will be "
                        "removed in a future panther version.", path)
