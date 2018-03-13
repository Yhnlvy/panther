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

# python recursion limit
RECURSION_LIMIT = 4000

# excluded path by default
NODE_MODULES = 'node_modules'

# default plugin name pattern
plugin_name_pattern = '*.py'

# default progress increment
progress_increment = 50

RANKING = ['UNDEFINED', 'LOW', 'MEDIUM', 'HIGH']
RANKING_VALUES = {'UNDEFINED': 1, 'LOW': 3, 'MEDIUM': 5, 'HIGH': 10}
CRITERIA = [('SEVERITY', 'UNDEFINED'), ('CONFIDENCE', 'UNDEFINED')]

# add each ranking to globals, to allow direct access in module name space
for rank in RANKING:
    globals()[rank] = rank

CONFIDENCE_DEFAULT = 'UNDEFINED'

# override with "log_format" option in config file
log_format_string = '[%(module)s]\t%(levelname)s\t%(message)s'
