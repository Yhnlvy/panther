# Copyright (c) 2015 VMware, Inc.
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

import os
import subprocess

import testtools


class RuntimeTests(testtools.TestCase):

    def _test_runtime(self, cmdlist, infile=None):
        process = subprocess.Popen(
            cmdlist,
            stdin=infile if infile else subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True
        )
        stdout, stderr = process.communicate()
        retcode = process.poll()
        return (retcode, stdout.decode('utf-8'))

    def _test_example(self, cmdlist, targets):
        for t in targets:
            cmdlist.append(os.path.join(os.getcwd(), 'examples', t))
        return self._test_runtime(cmdlist)

    def test_no_arguments(self):
        (retcode, output) = self._test_runtime(['panther', ])
        self.assertEqual(2, retcode)
        self.assertIn("No targets found in CLI or ini files", output)

    def test_piped_input(self):
        with open('examples/eval.js', 'r') as infile:
            (retcode, output) = self._test_runtime(['panther', '-'], infile)
            self.assertEqual(1, retcode)
            self.assertIn("Total lines of code: 2", output)
            self.assertIn("Low: 0", output)
            self.assertIn("High: 1", output)
            self.assertIn("Files skipped (0):", output)
            self.assertIn("Issue: [P601:eval_used]", output)
            self.assertIn("<stdin>:3", output)

    def test_nonexistent_config(self):
        (retcode, output) = self._test_runtime([
            'panther', '-c', 'nonexistent.yml', 'xx.py'
        ])
        self.assertEqual(2, retcode)
        self.assertIn("nonexistent.yml : Could not read config file.", output)

    def test_help_arg(self):
        (retcode, output) = self._test_runtime(['panther', '-h'])
        self.assertEqual(0, retcode)
        self.assertIn(
            "Panther - a Python source code security analyzer", output
        )
        self.assertIn("usage: panther [-h]", output)
        self.assertIn("positional arguments:", output)
        self.assertIn("optional arguments:", output)
        self.assertIn("tests were discovered and loaded:", output)

    # test examples (use _test_example() to wrap in config location argument
    def test_example_nonexistent(self):
        (retcode, output) = self._test_example(
            ['panther', ], ['nonexistent.py', ]
        )
        self.assertEqual(0, retcode)
        self.assertIn("Files skipped (1):", output)
        self.assertIn("nonexistent.py (No such file or directory", output)

    def test_example_okay(self):
        (retcode, output) = self._test_example(['panther', ], ['okay.js', ])
        self.assertEqual(0, retcode)
        self.assertIn("Total lines of code: 1", output)
        self.assertIn("Files skipped (0):", output)
        self.assertIn("No issues identified.", output)

    def test_example_nonsense(self):
        (retcode, output) = self._test_example(['panther', ], ['nonsense.js', ])
        self.assertEqual(0, retcode)
        self.assertIn("Files skipped (1):", output)
        self.assertIn("Exception occurred when executing tests against", output)
