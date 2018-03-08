# Copyright (c) 2017 VMware, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import collections
import tempfile

import mock
import testtools
import yaml

import panther
from panther.core import config
from panther.core import constants
from panther.core import issue
from panther.core import manager
from panther.core import metrics
from panther.formatters import json as p_json


class JsonFormatterTests(testtools.TestCase):

    def setUp(self):
        super(JsonFormatterTests, self).setUp()
        conf = config.PantherConfig()
        self.manager = manager.PantherManager(conf, 'file')
        (tmp_fd, self.tmp_fname) = tempfile.mkstemp()
        self.context = {'filename': self.tmp_fname,
                        'lineno': 4,
                        'linerange': [4]}
        self.check_name = 'hardcoded_bind_all_interfaces'
        self.issue = issue.Issue(panther.MEDIUM, panther.MEDIUM,
                                 'Possible binding to all interfaces.')

        self.candidates = [issue.Issue(panther.LOW, panther.LOW, 'Candidate A',
                                       lineno=1),
                           issue.Issue(panther.HIGH, panther.HIGH, 'Candiate B',
                                       lineno=2)]

        self.manager.out_file = self.tmp_fname

        self.issue.fname = self.context['filename']
        self.issue.lineno = self.context['lineno']
        self.issue.linerange = self.context['linerange']
        self.issue.test = self.check_name

        self.manager.results.append(self.issue)
        self.manager.metrics = metrics.Metrics()

        # mock up the metrics
        for key in ['_totals', 'binding.py']:
            self.manager.metrics.data[key] = {'loc': 4, 'nosec': 2}
            for (criteria, default) in constants.CRITERIA:
                for rank in constants.RANKING:
                    self.manager.metrics.data[key]['{0}.{1}'.format(
                        criteria, rank
                    )] = 0

    @mock.patch('panther.core.manager.PantherManager.get_issue_list')
    def test_report(self, get_issue_list):
        self.manager.files_list = ['binding.py']
        self.manager.scores = [{'SEVERITY': [0] * len(constants.RANKING),
                                'CONFIDENCE': [0] * len(constants.RANKING)}]

        get_issue_list.return_value = collections.OrderedDict(
            [(self.issue, self.candidates)])

        tmp_file = open(self.tmp_fname, 'w')
        p_json.report(self.manager, tmp_file, self.issue.severity,
                      self.issue.confidence)

        with open(self.tmp_fname) as f:
            data = yaml.load(f.read())
            self.assertIsNotNone(data['generated_at'])
            self.assertEqual(self.tmp_fname, data['results'][0]['filename'])
            self.assertEqual(self.issue.severity,
                             data['results'][0]['issue_severity'])
            self.assertEqual(self.issue.confidence,
                             data['results'][0]['issue_confidence'])
            self.assertEqual(self.issue.text, data['results'][0]['issue_text'])
            self.assertEqual(self.context['lineno'],
                             data['results'][0]['line_number'])
            self.assertEqual(self.context['linerange'],
                             data['results'][0]['line_range'])
            self.assertEqual(self.check_name, data['results'][0]['test_name'])
            self.assertIn('candidates', data['results'][0])
            self.assertIn('more_info', data['results'][0])
            self.assertIsNotNone(data['results'][0]['more_info'])
