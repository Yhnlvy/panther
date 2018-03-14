# -*- coding:utf-8 -*-

# #############################################################################
# Panther Baseline is a tool that runs Panther against a Git commit, and compares
# the current commit findings to the parent commit findings.

# To do this it checks out the parent commit, runs Panther (with any provided
# filters or profiles), checks out the current commit, runs Panther, and then
# reports on any new findings.
# #############################################################################

import argparse
import contextlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile

import git

panther_args = sys.argv[1:]
baseline_tmp_file = '_panther_baseline_run.json'
commit_sha = None
default_output_format = 'terminal'
LOG = logging.getLogger(__name__)
repo = None
report_basename = 'panther_baseline_result'
valid_baseline_formats = ['txt', 'html', 'json']


def main():
    # our cleanup function needs this and can't be passed arguments
    global commit_sha
    global repo

    parent_commit_sha = None
    output_format = None
    repo = None
    report_fname = None

    init_logger()

    output_format, repo, report_fname, commit_sha, diff_only = initialize()

    if not repo:
        sys.exit(2)

    # #################### Find current and parent commits ####################
    try:
        commit = repo.commit(commit_sha)
        commit_sha = commit.hexsha
        LOG.info('Got current commit: [%s]', commit.name_rev)

        parent_commit = commit.parents[0]
        parent_commit_sha = parent_commit.hexsha
        LOG.info('Got parent commit: [%s]', parent_commit.name_rev)

    except git.BadName:
        LOG.error("Unable to get commit %s", commit_sha)
        sys.exit(2)
    except git.GitCommandError:
        LOG.error("Unable to get current or parent commit")
        sys.exit(2)
    except IndexError:
        LOG.error("Parent commit not available")
        sys.exit(2)

    # ################### Run Panther against both commits ###################
    output_type = (['-f', 'txt'] if output_format == default_output_format
                   else ['-o', report_fname])

    if diff_only:
        repo.head.reset(commit=commit_sha, working_tree=True)
        changed_files = list(commit.stats.files.keys())
        if not changed_files:
            LOG.info("No changes since last commit. Exiting...")
            sys.exit(2)

        LOG.info("Running analysis on the following files: \n%s", '\n'.join(changed_files))
        panther_args = _remove_recursive_from_args()

        panther_command = ['panther'] + changed_files + panther_args + output_type
        output, return_code = _run_command(panther_command)
    else:                   
        with baseline_setup() as t:

            panther_tmpfile = "{}/{}".format(t, baseline_tmp_file)

            steps = [{'message': 'Getting Panther baseline results',
                    'commit_sha': parent_commit_sha,
                    'args': panther_args + ['-f', 'json', '-o', panther_tmpfile]},

                    {'message': 'Comparing Panther results to baseline',
                    'commit_sha': commit_sha,
                    'args': panther_args + ['-b', panther_tmpfile] + output_type}]

            return_code = None

            for step in steps:
                repo.head.reset(commit=step['commit_sha'], working_tree=True)
                LOG.info(step['message'])

                panther_command = ['panther'] + step['args']
                output, return_code = _run_command(panther_command)
    # #################### Output and exit ####################################
    # print output or display message about written report
    if output_format == default_output_format:
        print(output)
    else:
        LOG.info("Successfully wrote %s", report_fname)

    # exit with the code the last Panther run returned
    sys.exit(return_code)


# #################### Clean up before exit ###################################
@contextlib.contextmanager
def baseline_setup():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, True)

    if repo:
        repo.head.reset(commit=commit_sha, working_tree=True)


# #################### Setup logging ##########################################
def init_logger():
    LOG.handlers = []
    log_level = logging.INFO
    log_format_string = "[%(levelname)7s ] %(message)s"
    logging.captureWarnings(True)
    LOG.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format_string))
    LOG.addHandler(handler)


# #################### Perform initialization and validate assumptions ########
def initialize():
    valid = True

    # #################### Parse Args #########################################
    parser = argparse.ArgumentParser(
        description='Panther Baseline - Generates Panther results compared to "'
                    'a baseline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Additional Panther arguments such as severity filtering (-ll) '
               'can be added and will be passed to Panther.'
    )

    parser.add_argument(
        'targets', metavar='targets', type=str, nargs='+',
        help='source file(s) or directory(s) to be tested'
    )

    parser.add_argument(
        '-f', dest='output_format', action='store',
        default='terminal', help='specify output format',
        choices=valid_baseline_formats
    )

    parser.add_argument(
        '-c', '--commit', dest='commit_sha',
        action='store', default=None, type=str,
        help='commit sha to be tested'
    )

    parser.add_argument(
        '--diff-only', dest='diff_only', action='store_true',
        help='runs analysis on changed files only'
    )

    args, unknown = parser.parse_known_args()
    # #################### Setup Output #######################################
    # set the output format, or use a default if not provided
    output_format = (args.output_format if args.output_format
                     else default_output_format)

    if output_format == default_output_format:
        LOG.info("No output format specified, using %s", default_output_format)

    # set the report name based on the output format
    report_fname = "{}.{}".format(report_basename, output_format)

    # #################### Handle Commit #######################################
    commit_sha = args.commit_sha

    if commit_sha:
        c_idx = panther_args.index(commit_sha)
        panther_args[c_idx - 1:c_idx + 1] = []

    # #################### Check Requirements #################################
    try:
        repo = git.Repo(os.getcwd())

    except git.exc.InvalidGitRepositoryError:
        LOG.error("Panther baseline must be called from a git project root")
        valid = False

    except git.exc.GitCommandNotFound:
        LOG.error("Git command not found")
        valid = False

    else:
        if repo.is_dirty():
            LOG.error("Current working directory is dirty and must be "
                      "resolved")
            valid = False

    # if output format is specified, we need to be able to write the report
    if output_format != default_output_format and os.path.exists(report_fname):
        LOG.error("File %s already exists, aborting", report_fname)
        valid = False

    # Panther needs to be able to create this temp file
    if os.path.exists(baseline_tmp_file):
        LOG.error("Temporary file %s needs to be removed prior to running",
                  baseline_tmp_file)
        valid = False

    # #################### Scan Mode #######################################
    diff_only = args.diff_only

    if diff_only:
        panther_args.remove('--diff-only')

    # we must validate -o is not provided, as it will mess up Panther baseline
    if '-o' in panther_args:
        LOG.error("Panther baseline must not be called with the -o option")
        valid = False

    return (
        output_format,
        repo,
        report_fname,
        commit_sha,
        diff_only
    ) if valid else (None, None, None, None, None)


# #################### Run the panther cli commands ########
def _run_command(cmd):
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        output = e.output
        return_code = e.returncode
    else:
        return_code = 0
        output = output.decode('utf-8')  # subprocess returns bytes

    if return_code not in [0, 1]:
        LOG.error("Error running command: %s\nOutput: %s\n",
                panther_args, output)
    return output, return_code


# #################### Removes the recursive flag for the --diff-only mode ########
def _remove_recursive_from_args():
    if '-r' in panther_args:
        index = panther_args.index('-r')
    if '--recursive' in panther_args:
        index = panther_args.index('--recursive')
    if index is not None:
        panther_args[index:index + 2] = []
    return panther_args


if __name__ == '__main__':
    main()
