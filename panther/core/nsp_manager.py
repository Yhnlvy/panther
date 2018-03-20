# -*- coding:utf-8 -*-

import json
import logging
import os
from subprocess import DEVNULL, CalledProcessError, call, check_output  # noqa

import panther
from panther.core import constants
from panther.core import issue

LOG = logging.getLogger(__name__)

SUCCESS_CODE = 0

"""
The nsp CLI tool exits with the following codes to signify state:

0: command ran with success
1: command run was 'check', was successful, but returned vulnerabilities outside of the threshold or filter
2: command received a server error (5xx)
3: unknown error
4: there was an error in the output reporter
"""


class NspManager(object):
    def __init__(self, results=None):
        '''Initialize the class with the tests manager results'''
        self.nsp_report = {}
        self.results = results

    @property
    def has_nsp(self):
        '''Return True if nsp is installed globally on the machine'''
        try:
            return_code = call('nsp --version', shell=True,
                               stdout=DEVNULL, stderr=DEVNULL)
        except Exception as e:
            LOG.error(e)
            return False
        return return_code == SUCCESS_CODE

    def run_check(self):
        '''Run the scan and return the output in json format'''
        if self.has_nsp:
            try:
                check_output(
                    'nsp check %s --reporter json' % os.getcwd(),
                    shell=True, stderr=DEVNULL
                )
            except CalledProcessError as e:
                if e.returncode == 1:
                    self.nsp_report = json.loads(e.output)
                    return True
            except Exception as e:
                pass
        return False

    @staticmethod
    def _format_issue_desc(vuln):
        '''Format the description of the issue'''
        msg = "Vulnerable version: {vv}\nPatched versions: {pv}\nRecommendation:\n{reco}"
        issue_desc = msg.format(
            vv=vuln['vulnerable_versions'],
            pv=vuln['patched_versions'],
            reco=vuln['recommendation']
        )
        return issue_desc

    @staticmethod
    def _format_issue_name(vuln):
        '''Format the title of the issue'''
        return "%s (%s@%s)" % (vuln['title'], vuln['module'], vuln['version'])

    @staticmethod
    def _get_severity_level(vuln):
        '''Computes the severity level based on the CVSS score'''
        level = panther.MEDIUM
        cvss_score = vuln['cvss_score']
        if cvss_score < 4:
            level = panther.LOW
        if cvss_score > 7:
            level = panther.HIGH
        return level

    def update_issues(self):
        '''Updates the issues with dependencies vulnerabilities'''
        if self.run_check():
            for vuln in self.nsp_report:
                i = issue.Issue(None)
                i.from_dict({
                    'filename': 'package.json',
                    'test_id': constants.NSP_TEST_ID,
                    'line_number': '',
                    'line_range': [0, 1],
                    'test_name': NspManager._format_issue_name(vuln),
                    'issue_text': ' > '.join(vuln['path']),
                    'code': NspManager._format_issue_desc(vuln),
                    'issue_confidence': panther.HIGH,
                    'issue_severity': NspManager._get_severity_level(vuln)
                })
                self.results.append(i)
