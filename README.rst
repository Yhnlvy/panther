Panther
======

.. image:: https://circleci.com/gh/Yhnlvy/panther.svg?style=svg
    :target: https://circleci.com/gh/Yhnlvy/panther

Overview
--------
Panther is a tool designed to find common security issues in Node.js code. To do
this Panther processes each file, builds an AST from it, and runs appropriate
plugins against the AST nodes. Once Panther has finished scanning all the files
it generates a report.

Installation
------------
Panther is distributed on PyPI. The best way to install it is with pip:


Create a virtual environment (optional)::

    virtualenv panther-env

Install Panther::

    pip install panther
    # Or if you're working with a Python 3.5 project
    pip3.5 install panther

Run Panther::

    panther -r path/to/your/code


Panther can also be installed from source. To do so, download the source tarball
from PyPI, then install it::

    python setup.py install


Usage
-----
Example usage across a code tree::

    panther -r ~/itc-repo/keystone

Example usage across the ``examples/`` directory, showing three lines of
context and only reporting on the high-severity issues::

    panther examples/*.py -n 3 -lll

Panther can be run with profiles. To run Panther against the examples directory
using only the plugins listed in the ``ShellInjection`` profile::

    panther examples/*.py -p ShellInjection

Panther also supports passing lines of code to scan using standard input. To
run Panther with standard input::

    cat examples/imports.py | panther -

Usage::

    $ panther -h
    usage: panther [-h] [-r] [-a {file,vuln}] [-n CONTEXT_LINES] [-c CONFIG_FILE]
                  [-p PROFILE] [-t TESTS] [-s SKIPS] [-l] [-i]
                  [-f {csv,custom,html,json,screen,txt,xml,yaml}]
                  [--msg-template MSG_TEMPLATE] [-o [OUTPUT_FILE]] [-v] [-d]
                  [--ignore-nosec] [-x EXCLUDED_PATHS] [-b BASELINE]
                  [--ini INI_PATH] [--version]
                  [targets [targets ...]]

    Panther - a Node.js source code security analyzer

    positional arguments:
      targets               source file(s) or directory(s) to be tested

    optional arguments:
      -h, --help            show this help message and exit
      -r, --recursive       find and process files in subdirectories
      -a {file,vuln}, --aggregate {file,vuln}
                            aggregate output by vulnerability (default) or by
                            filename
      -n CONTEXT_LINES, --number CONTEXT_LINES
                            maximum number of code lines to output for each issue
      -c CONFIG_FILE, --configfile CONFIG_FILE
                            optional config file to use for selecting plugins and
                            overriding defaults
      -p PROFILE, --profile PROFILE
                            profile to use (defaults to executing all tests)
      -t TESTS, --tests TESTS
                            comma-separated list of test IDs to run
      -s SKIPS, --skip SKIPS
                            comma-separated list of test IDs to skip
      -l, --level           report only issues of a given severity level or higher
                            (-l for LOW, -ll for MEDIUM, -lll for HIGH)
      -i, --confidence      report only issues of a given confidence level or
                            higher (-i for LOW, -ii for MEDIUM, -iii for HIGH)
      -f {csv,custom,html,json,screen,txt,xml,yaml}, --format {csv,custom,html,json,screen,txt,xml,yaml}
                            specify output format
      --msg-template        MSG_TEMPLATE
                            specify output message template (only usable with
                            --format custom), see CUSTOM FORMAT section for list
                            of available values
      -o [OUTPUT_FILE], --output [OUTPUT_FILE]
                            write report to filename
      -v, --verbose         output extra information like excluded and included
                            files
      -d, --debug           turn on debug mode
      --ignore-nosec        do not skip lines with # nosec comments
      -x EXCLUDED_PATHS, --exclude EXCLUDED_PATHS
                            comma-separated list of paths to exclude from scan
                            (note that these are in addition to the excluded paths
                            provided in the config file)
      -b BASELINE, --baseline BASELINE
                            path of a baseline report to compare against (only
                            JSON-formatted files are accepted)
      --ini INI_PATH        path to a .panther file that supplies command line
                            arguments
      --version             show program's version number and exit

    CUSTOM FORMATTING
    -----------------

    Available tags:

        {abspath}, {relpath}, {line},  {test_id},
        {severity}, {msg}, {confidence}, {range}

    Example usage:

        Default template:
        panther -r examples/ --format custom --msg-template \
        "{abspath}:{line}: {test_id}[panther]: {severity}: {msg}"

        Provides same output as:
        panther -r examples/ --format custom

        Tags can also be formatted in python string.format() style:
        panther -r examples/ --format custom --msg-template \
        "{relpath:20.20s}: {line:03}: {test_id:^8}: DEFECT: {msg:>20}"

        See python documentation for more information about formatting style:
        https://docs.python.org/3.4/library/string.html

    The following tests were discovered and loaded:
    -----------------------------------------------

      P601  server_side_injection
      P602  sql_injection


Baseline Usage
-----
Example usage across a code tree::

    panther-baseline -r app --diff-only -c 6ce647fd

Usage::

    $ panther-baseline -h
    usage: panther-baseline [-h] [-f {txt,html,json}] [-c COMMIT_SHA]
                        [--diff-only]
                        targets [targets ...]

    Panther Baseline - Generates Panther results compared to a baseline

    positional arguments:
    targets               source file(s) or directory(s) to be tested

    optional arguments:
    -h, --help            show this help message and exit
    -f {txt,html,json}    specify output format
    -c COMMIT_SHA, --commit COMMIT_SHA
                            commit sha to be tested
    --diff-only           run analysis on changed files only

    Additional Panther arguments such as severity filtering (-ll) can be added and will be passed to Panther.

Configuration
-------------
An optional config file may be supplied and may include:
 - lists of tests which should or shouldn't be run
 - exclude_dirs - sections of the path, that if matched, will be excluded from
   scanning
 - overridden plugin settings - may provide different settings for some
   plugins

Per Project Command Line Args
-----------------------------
Projects may include a `.panther` file that specifies command line arguments
that should be supplied for that project. The currently supported arguments
are:

 - targets: comma separated list of target dirs/files to run panther on
 - exclude: comma separated list of excluded paths
 - skips: comma separated list of tests to skip
 - tests: comma separated list of tests to run

To use this, put a .panther file in your project's directory. For example:

::

   [panther]
   exclude: /test

::

   [panther]
   tests: P601,P602


Exclusions
----------
In the event that a line of code triggers a Panther issue, but that the line
has been reviewed and the issue is a false positive or acceptable for some
other reason, the line can be marked with a ``# nosec`` and any results
associated with it will not be reported.

For example, although this line may cause Panther to report a potential
security issue, it will not be reported::

    self.process = subprocess.Popen('/bin/echo', shell=True)  # nosec


Vulnerability Tests
-------------------
Vulnerability tests or "plugins" are defined in files in the plugins directory.

Tests are written in Python and are autodiscovered from the plugins directory.
Each test can examine one or more type of Python statements. Tests are marked
with the types of Python statements they examine (for example: function call,
string, import, etc).

Tests are executed by the ``PantherNodeVisitor`` object as it visits each node
in the AST.

Test results are maintained in the ``PantherResultStore`` and aggregated for
output at the completion of a test run.


Writing Tests
-------------
To write a test:
 - Identify a vulnerability to build a test for, and create a new file in
   examples/ that contains one or more cases of that vulnerability.
 - Consider the vulnerability you're testing for, mark the function with one
   or more of the appropriate decorators:
   - @checks('Call')
   - @checks('Import', 'ImportFrom')
   - @checks('Str')
 - Create a new Python source file to contain your test, you can reference
   existing tests for examples.
 - The function that you create should take a parameter "context" which is
   an instance of the context class you can query for information about the
   current element being examined.  You can also get the raw AST node for
   more advanced use cases.  Please see the context.py file for more.
 - Extend your Panther configuration file as needed to support your new test.
 - Execute Panther against the test file you defined in examples/ and ensure
   that it detects the vulnerability.  Consider variations on how this
   vulnerability might present itself and extend the example file and the test
   function accordingly.


Extending Panther
----------------

Panther allows users to write and register extensions for checks and formatters.
Panther will load plugins from two entry-points:

- `panther.formatters`
- `panther.plugins`

Formatters need to accept 4 things:

- `result_store`: An instance of `panther.core.PantherResultStore`
- `file_list`: The list of files which were inspected in the scope
- `scores`: The scores awarded to each file in the scope
- `excluded_files`: The list of files that were excluded from the scope

Plugins tend to take advantage of the `panther.checks` decorator which allows
the author to register a check for a particular type of AST node. For example

::

    @panther.checks('Call')
    def prohibit_unsafe_deserialization(context):
        if 'unsafe_load' in context.call_function_name_qual:
            return panther.Issue(
                severity=panther.HIGH,
                confidence=panther.HIGH,
                text="Unsafe deserialization detected."
            )

To register your plugin, you have two options:

1. If you're using setuptools directly, add something like the following to
   your ``setup`` call::

        # If you have an imaginary bson formatter in the panther_bson module
        # and a function called `formatter`.
        entry_points={'panther.formatters': ['bson = panther_bson:formatter']}
        # Or a check for using mako templates in panther_mako that
        entry_points={'panther.plugins': ['mako = panther_mako']}

2. If you're using pbr, add something like the following to your `setup.cfg`
   file::

        [entry_points]
        panther.formatters =
            bson = panther_bson:formatter
        panther.plugins =
            mako = panther_mako

Contributing
------------

You can test any changes with tox::

    pip install tox
    tox -e debug
    tox -e pep8
