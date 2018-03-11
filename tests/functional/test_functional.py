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

import os

import six
import testtools

from panther.core import config as p_config
from panther.core import constants as C
from panther.core import manager as p_manager
from panther.core import metrics
from panther.core import test_set as p_test_set


class FunctionalTests(testtools.TestCase):

    '''Functional tests for panther test plugins.

    This set of tests runs panther against each example file in turn
    and records the score returned. This is compared to a known good value.
    When new tests are added to an example the expected result should be
    adjusted to match.
    '''

    def setUp(self):
        super(FunctionalTests, self).setUp()
        # NOTE(tkelsey): panther is very sensitive to paths, so stitch
        # them up here for the testing environment.
        #
        path = os.path.join(os.getcwd(), 'panther', 'plugins')
        p_conf = p_config.PantherConfig()
        self.p_mgr = p_manager.PantherManager(p_conf, 'file')
        self.p_mgr.p_conf._settings['plugins_dir'] = path
        self.p_mgr.p_ts = p_test_set.PantherTestSet(config=p_conf)

    def run_example(self, example_script, ignore_nosec=False):
        '''A helper method to run the specified test

        This method runs the test, which populates the self.p_mgr.scores
        value. Call this directly if you need to run a test, but do not
        need to test the resulting scores against specified values.
        :param example_script: Filename of an example script to test
        '''
        path = os.path.join(os.getcwd(), 'examples', example_script)
        self.p_mgr.ignore_nosec = ignore_nosec
        self.p_mgr.discover_files([path], True)
        self.p_mgr.run_tests()

    def check_example(self, example_script, expect, ignore_nosec=False):
        '''A helper method to test the scores for example scripts.

        :param example_script: Filename of an example script to test
        :param expect: dict with expected counts of issue types
        '''
        # reset scores for subsequent calls to check_example
        self.p_mgr.scores = []
        self.run_example(example_script, ignore_nosec=ignore_nosec)

        result = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        }

        for test_scores in self.p_mgr.scores:
            for score_type in test_scores:
                self.assertIn(score_type, expect)
                for idx, rank in enumerate(C.RANKING):
                    result[score_type][rank] = (test_scores[score_type][idx] /
                                                C.RANKING_VALUES[rank])

        self.assertDictEqual(expect, result)

    def check_metrics(self, example_script, expect):
        '''A helper method to test the metrics being returned.

        :param example_script: Filename of an example script to test
        :param expect: dict with expected values of metrics
        '''
        self.p_mgr.metrics = metrics.Metrics()
        self.p_mgr.scores = []
        self.run_example(example_script)

        # test general metrics (excludes issue counts)
        m = self.p_mgr.metrics.data
        for k in expect:
            if k != 'issues':
                self.assertEqual(expect[k], m['_totals'][k])
        # test issue counts
        if 'issues' in expect:
            for (criteria, default) in C.CRITERIA:
                for rank in C.RANKING:
                    label = '{0}.{1}'.format(criteria, rank)
                    expected = 0
                    if expect['issues'].get(criteria).get(rank):
                        expected = expect['issues'][criteria][rank]
                    self.assertEqual(expected, m['_totals'][label])

    def test_eval(self):
        '''Test the `eval` example.'''
        expect = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 1, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 1, 'HIGH': 0}
        }
        self.check_example('eval.js', expect)

    def test_nonsense(self):
        '''Test that a syntactically invalid module is skipped.'''
        self.run_example('nonsense.js')
        self.assertEqual(1, len(self.p_mgr.skipped))

    def test_okay(self):
        '''Test a vulnerability-free file.'''
        expect = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        }
        self.check_example('okay.js', expect)

    def test_subdirectory_okay(self):
        '''Test a vulnerability-free file under a subdirectory.'''
        expect = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        }
        self.check_example('init-js-test/subdirectory-okay.js', expect)

    def test_ignore_skip(self):
        '''Test --ignore-nosec flag.'''
        expect = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 1, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 1, 'HIGH': 0}
        }
        self.check_example('nosec.js', expect, ignore_nosec=True)

    def test_code_line_numbers(self):
        self.run_example('eval.js')
        issues = self.p_mgr.get_issue_list()

        code_lines = issues[0].get_code().splitlines()
        lineno = issues[0].lineno
        self.assertEqual("%i " % (lineno - 1), code_lines[0][:2])
        self.assertEqual("%i " % (lineno), code_lines[1][:2])

    def test_nosec(self):
        expect = {
            'SEVERITY': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0},
            'CONFIDENCE': {'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        }
        self.check_example('nosec.js', expect)
