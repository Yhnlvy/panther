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

import collections
import fnmatch
import json
import logging
import os
import sys
import traceback

from panther.core import constants as p_constants
from panther.core import extension_loader
from panther.core import issue
from panther.core import meta_ast as p_meta_ast
from panther.core import metrics
from panther.core import node_visitor as p_node_visitor
from panther.core import test_set as p_test_set


LOG = logging.getLogger(__name__)

class PantherManager(object):

    scope = []

    def __init__(self, config, agg_type, debug=False, verbose=False,
                 profile=None, ignore_nosec=False):
        '''Get logger, config, AST handler, and result store ready

        :param config: config options object
        :type config: panther.core.PantherConfig
        :param agg_type: aggregation type
        :param debug: Whether to show debug messages or not
        :param verbose: Whether to show verbose output
        :param profile_name: Optional name of profile to use (from cmd line)
        :param ignore_nosec: Whether to ignore #nosec or not
        :return:
        '''
        self.debug = debug
        self.verbose = verbose
        if not profile:
            profile = {}
        self.ignore_nosec = ignore_nosec
        self.p_conf = config
        self.files_list = []
        self.excluded_files = []
        self.p_ma = p_meta_ast.PantherMetaAst()
        self.skipped = []
        self.results = []
        self.baseline = []
        self.agg_type = agg_type
        self.metrics = metrics.Metrics()
        self.p_ts = p_test_set.PantherTestSet(config, profile)

        # set the increment of after how many files to show progress
        self.progress = p_constants.progress_increment
        self.scores = []

    def get_skipped(self):
        ret = []
        # "skip" is a tuple of name and reason, decode just the name
        for skip in self.skipped:
            if isinstance(skip[0], bytes):
                ret.append((skip[0].decode('utf-8'), skip[1]))
            else:
                ret.append(skip)
        return ret

    def get_issue_list(self,
                       sev_level=p_constants.LOW,
                       conf_level=p_constants.LOW):
        return self.filter_results(sev_level, conf_level)

    def populate_baseline(self, data):
        '''Populate a baseline set of issues from a JSON report

        This will populate a list of baseline issues discovered from a previous
        run of panther. Later this baseline can be used to filter out the result
        set, see filter_results.
        '''
        items = []
        try:
            jdata = json.loads(data)
            items = [issue.issue_from_dict(j) for j in jdata["results"]]
        except Exception as e:
            LOG.warning("Failed to load baseline data: %s", e)
        self.baseline = items

    def filter_results(self, sev_filter, conf_filter):
        '''Returns a list of results filtered by the baseline

        This works by checking the number of results returned from each file we
        process. If the number of results is different to the number reported
        for the same file in the baseline, then we return all results for the
        file. We can't reliably return just the new results, as line numbers
        will likely have changed.

        :param sev_filter: severity level filter to apply
        :param conf_filter: confidence level filter to apply
        '''

        results = [i for i in self.results if
                   i.filter(sev_filter, conf_filter)]

        if not self.baseline:
            return results

        unmatched = _compare_baseline_results(self.baseline, results)
        # if it's a baseline we'll return a dictionary of issues and a list of
        # candidate issues
        return _find_candidate_matches(unmatched, results)

    def results_count(self, sev_filter=p_constants.LOW,
                      conf_filter=p_constants.LOW):
        '''Return the count of results

        :param sev_filter: Severity level to filter lower
        :param conf_filter: Confidence level to filter
        :return: Number of results in the set
        '''
        return len(self.get_issue_list(sev_filter, conf_filter))

    def output_results(self, lines, sev_level, conf_level, output_file,
                       output_format, template=None):
        '''Outputs results from the result store

        :param lines: How many surrounding lines to show per result
        :param sev_level: Which severity levels to show (LOW, MEDIUM, HIGH)
        :param conf_level: Which confidence levels to show (LOW, MEDIUM, HIGH)
        :param output_file: File to store results
        :param output_format: output format plugin name
        :param template: Output template with non-terminal tags <N>
                         (default:  {abspath}:{line}:
                         {test_id}[panther]: {severity}: {msg})
        :return: -
        '''
        try:
            formatters_mgr = extension_loader.MANAGER.formatters_mgr
            if output_format not in formatters_mgr:
                output_format = 'screen' if sys.stdout.isatty() else 'txt'

            formatter = formatters_mgr[output_format]
            report_func = formatter.plugin
            if output_format == 'custom':
                report_func(self, fileobj=output_file, sev_level=sev_level,
                            conf_level=conf_level, lines=lines,
                            template=template)
            else:
                report_func(self, fileobj=output_file, sev_level=sev_level,
                            conf_level=conf_level, lines=lines)

        except Exception as e:
            raise RuntimeError("Unable to output report using '%s' formatter: "
                               "%s" % (output_format, str(e)))

    def discover_files(self, targets, recursive=False, excluded_paths=''):
        '''Add tests directly and from a directory to the test set

        :param targets: The command line list of files and directories
        :param recursive: True/False - whether to add all files from dirs
        :return:
        '''
        # We'll mantain a list of files which are added, and ones which have
        # been explicitly excluded
        files_list = set()
        excluded_files = set()

        excluded_path_strings = self.p_conf.get_option('exclude_dirs') or []
        excluded_path_strings.append(p_constants.NODE_MODULES)
        included_globs = self.p_conf.get_option('include') or ['*.py']

        # if there are command line provided exclusions add them to the list
        if excluded_paths:
            for path in excluded_paths.split(','):
                excluded_path_strings.append(path)

        # build list of files we will analyze
        for fname in targets:
            # if this is a directory and recursive is set, find all files
            if os.path.isdir(fname):
                if recursive:
                    new_files, newly_excluded = _get_files_from_dir(
                        fname,
                        included_globs=included_globs,
                        excluded_path_strings=excluded_path_strings
                    )
                    files_list.update(new_files)
                    excluded_files.update(newly_excluded)
                else:
                    LOG.warning("Skipping directory (%s), use -r flag to "
                                "scan contents", fname)

            else:
                # if the user explicitly mentions a file on command line,
                # we'll scan it, regardless of whether it's in the included
                # file types list
                if _is_file_included(fname, included_globs,
                                     excluded_path_strings,
                                     enforce_glob=False):
                    files_list.add(fname)
                else:
                    excluded_files.add(fname)

        self.files_list = sorted(files_list)
        self.excluded_files = sorted(excluded_files)

    def run_tests(self):
        '''Runs through all files in the scope

        :return: -
        '''
        # display progress, if number of files warrants it
        if len(self.files_list) > self.progress:
            sys.stderr.write("%s [" % len(self.files_list))

        # if we have problems with a file, we'll remove it from the files_list
        # and add it to the skipped list instead
        new_files_list = list(self.files_list)

        for count, fname in enumerate(self.files_list):
            LOG.debug("working on file : %s", fname)

            if len(self.files_list) > self.progress:
                # is it time to update the progress indicator?
                if count % self.progress == 0:
                    sys.stderr.write("%s.. " % count)
                    sys.stderr.flush()
            try:
                if fname == '-':
                    sys.stdin = os.fdopen(sys.stdin.fileno(), 'rb', 0)
                    self._parse_file('<stdin>', sys.stdin, new_files_list)
                else:
                    with open(fname, 'r') as fdata:
                        self._parse_file(fname, fdata, new_files_list)
            except IOError as e:
                self.skipped.append((fname, e.strerror))
                new_files_list.remove(fname)

        if len(self.files_list) > self.progress:
            sys.stderr.write("]\n")
            sys.stderr.flush()

        # reflect any files which may have been skipped
        self.files_list = new_files_list

        # do final aggregation of metrics
        self.metrics.aggregate()

    def _parse_file(self, fname, fdata, new_files_list):
        try:
            # parse the current file
            data = fdata.read()
            lines = data.splitlines()
            self.metrics.begin(fname)
            self.metrics.count_locs(lines)
            if self.ignore_nosec:
                nosec_lines = set()
            else:
                nosec_lines = set(
                    lineno + 1 for
                    (lineno, line) in enumerate(lines)
                    if '//nosec' in line or '// nosec' in line)
            score = self._execute_ast_visitor(fname, data, nosec_lines)
            self.scores.append(score)
            self.metrics.count_issues([score, ])
        except KeyboardInterrupt as e:
            sys.exit(2)
        except SyntaxError as e:
            self.skipped.append((fname,
                                 "syntax error while parsing AST from file"))
            new_files_list.remove(fname)
        except Exception as e:
            LOG.error("Exception occurred when executing tests against "
                      "%s. Run \"panther --debug %s\" to see the full "
                      "traceback.", fname, fname)
            self.skipped.append((fname, 'exception while scanning file'))
            new_files_list.remove(fname)
            LOG.debug("  Exception string: %s", e)
            LOG.debug("  Exception traceback: %s", traceback.format_exc())

    def _execute_ast_visitor(self, fname, data, nosec_lines):
        '''Execute AST parse on each file

        :param fname: The name of the file being parsed
        :param data: Original file contents
        :param lines: The lines of code to process
        :return: The accumulated test score
        '''
        score = []
        res = p_node_visitor.PantherNodeVisitor(fname, self.p_ma,
                                               self.p_ts, self.debug,
                                               nosec_lines, self.metrics)

        score = res.process(data)
        self.results.extend(res.tester.results)
        return score


def _get_files_from_dir(files_dir, included_globs=None,
                        excluded_path_strings=None):
    if not included_globs:
        included_globs = ['*.py']
    if not excluded_path_strings:
        excluded_path_strings = []

    files_list = set()
    excluded_files = set()

    for root, subdirs, files in os.walk(files_dir):
        for filename in files:
            path = os.path.join(root, filename)
            if _is_file_included(path, included_globs, excluded_path_strings):
                files_list.add(path)
            else:
                excluded_files.add(path)

    return files_list, excluded_files


def _is_file_included(path, included_globs, excluded_path_strings,
                      enforce_glob=True):
    '''Determine if a file should be included based on filename

    This utility function determines if a file should be included based
    on the file name, a list of parsed extensions, excluded paths, and a flag
    specifying whether extensions should be enforced.

    :param path: Full path of file to check
    :param parsed_extensions: List of parsed extensions
    :param excluded_paths: List of paths from which we should not include files
    :param enforce_glob: Can set to false to bypass extension check
    :return: Boolean indicating whether a file should be included
    '''
    return_value = False

    # if this is matches a glob of files we look at, and it isn't in an
    # excluded path
    if _matches_glop_list(path, included_globs) or not enforce_glob:
        if not any(x in path for x in excluded_path_strings):
            return_value = True

    return return_value


def _matches_glop_list(filename, glop_list):
    for glob in glop_list:
        if fnmatch.fnmatch(filename, glob):
            return True
    return False


def _compare_baseline_results(baseline, results):
    """Compare a baseline list of issues to list of results

    This function compares a baseline set of issues to a current set of issues
    to find results that weren't present in the baseline.

    :param baseline: Baseline list of issues
    :param results: Current list of issues
    :return: List of unmatched issues
    """
    return [a for a in results if a not in baseline]


def _find_candidate_matches(unmatched_issues, results_list):
    """Returns a dictionary with issue candidates

    For example, let's say we find a new command injection issue in a file
    which used to have two.  Panther can't tell which of the command injection
    issues in the file are new, so it will show all three.  The user should
    be able to pick out the new one.

    :param unmatched_issues: List of issues that weren't present before
    :param results_list: Master list of current Panther findings
    :return: A dictionary with a list of candidates for each issue
    """

    issue_candidates = collections.OrderedDict()

    for unmatched in unmatched_issues:
        issue_candidates[unmatched] = ([i for i in results_list if
                                        unmatched == i])

    return issue_candidates