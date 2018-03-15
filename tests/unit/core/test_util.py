# -*- coding:utf-8 -*-
#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
# Copyright 2015 Nebula, Inc.
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

import ast
import os
import shutil
import sys
import tempfile
import testtools

from panther.core.pyesprima import esprima
from panther.core import utils as p_utils
from panther.core import visitor

def _touch(path):
    '''Create an empty file at ``path``.'''
    newf = open(path, 'w')
    newf.close()


class UtilTests(testtools.TestCase):
    '''This set of tests exercises panther.core.util functions.'''

    def setUp(self):
        super(UtilTests, self).setUp()
        self._setup_get_module_qualname_from_path()

    def _setup_get_module_qualname_from_path(self):
        '''Setup a fake directory for testing get_module_qualname_from_path().

        Create temporary directory and then create fake .py files
        within directory structure.  We setup test cases for
        a typical module, a path misssing a middle __init__.py,
        no __init__.py anywhere in path, symlinking .py files.
        '''

        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)
        self.reltempdir = os.path.relpath(self.tempdir)

        # good/a/b/c/test_typical.py
        os.makedirs(os.path.join(
            self.tempdir, 'good', 'a', 'b', 'c'), 0o755)
        _touch(os.path.join(self.tempdir, 'good', '__init__.py'))
        _touch(os.path.join(self.tempdir, 'good', 'a', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'good', 'a', 'b', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'good', 'a', 'b', 'c', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'good', 'a', 'b', 'c', 'test_typical.py'))

        # missingmid/a/b/c/test_missingmid.py
        os.makedirs(os.path.join(
            self.tempdir, 'missingmid', 'a', 'b', 'c'), 0o755)
        _touch(os.path.join(self.tempdir, 'missingmid', '__init__.py'))
        # no missingmid/a/__init__.py
        _touch(os.path.join(
            self.tempdir, 'missingmid', 'a', 'b', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'missingmid', 'a', 'b', 'c', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'missingmid', 'a', 'b', 'c', 'test_missingmid.py'))

        # missingend/a/b/c/test_missingend.py
        os.makedirs(os.path.join(
            self.tempdir, 'missingend', 'a', 'b', 'c'), 0o755)
        _touch(os.path.join(
            self.tempdir, 'missingend', '__init__.py'))
        _touch(os.path.join(
            self.tempdir, 'missingend', 'a', 'b', '__init__.py'))
        # no missingend/a/b/c/__init__.py
        _touch(os.path.join(
            self.tempdir, 'missingend', 'a', 'b', 'c', 'test_missingend.py'))

        # syms/a/bsym/c/test_typical.py
        os.makedirs(os.path.join(self.tempdir, 'syms', 'a'), 0o755)
        _touch(os.path.join(self.tempdir, 'syms', '__init__.py'))
        _touch(os.path.join(self.tempdir, 'syms', 'a', '__init__.py'))
        os.symlink(os.path.join(self.tempdir, 'good', 'a', 'b'),
                   os.path.join(self.tempdir, 'syms', 'a', 'bsym'))

    def test_get_module_qualname_from_path_abs_typical(self):
        '''Test get_module_qualname_from_path with typical absolute paths.'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.tempdir, 'good', 'a', 'b', 'c', 'test_typical.py'))
        self.assertEqual('good.a.b.c.test_typical', name)

    def test_get_module_qualname_from_path_with_dot(self):
        '''Test get_module_qualname_from_path with a "." .'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            '.', '__init__.py'))

        self.assertEqual('__init__', name)

    def test_get_module_qualname_from_path_abs_missingmid(self):
        # Test get_module_qualname_from_path with missing module
        # __init__.py

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.tempdir, 'missingmid', 'a', 'b', 'c',
            'test_missingmid.py'))
        self.assertEqual('b.c.test_missingmid', name)

    def test_get_module_qualname_from_path_abs_missingend(self):
        # Test get_module_qualname_from_path with no __init__.py
        # last dir'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.tempdir, 'missingend', 'a', 'b', 'c',
            'test_missingend.py'))
        self.assertEqual('test_missingend', name)

    def test_get_module_qualname_from_path_abs_syms(self):
        '''Test get_module_qualname_from_path with symlink in path.'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.tempdir, 'syms', 'a', 'bsym', 'c', 'test_typical.py'))
        self.assertEqual('syms.a.bsym.c.test_typical', name)

    def test_get_module_qualname_from_path_rel_typical(self):
        '''Test get_module_qualname_from_path with typical relative paths.'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.reltempdir, 'good', 'a', 'b', 'c', 'test_typical.py'))
        self.assertEqual('good.a.b.c.test_typical', name)

    def test_get_module_qualname_from_path_rel_missingmid(self):
        # Test get_module_qualname_from_path with module __init__.py
        # missing and relative paths

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.reltempdir, 'missingmid', 'a', 'b', 'c',
            'test_missingmid.py'))
        self.assertEqual('b.c.test_missingmid', name)

    def test_get_module_qualname_from_path_rel_missingend(self):
        # Test get_module_qualname_from_path with __init__.py missing from
        # last dir and using relative paths

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.reltempdir, 'missingend', 'a', 'b', 'c',
            'test_missingend.py'))
        self.assertEqual('test_missingend', name)

    def test_get_module_qualname_from_path_rel_syms(self):
        '''Test get_module_qualname_from_path with symbolic relative paths.'''

        name = p_utils.get_module_qualname_from_path(os.path.join(
            self.reltempdir, 'syms', 'a', 'bsym', 'c', 'test_typical.py'))
        self.assertEqual('syms.a.bsym.c.test_typical', name)

    def test_get_module_qualname_from_path_sys(self):
        '''Test get_module_qualname_from_path with system module paths.'''

        name = p_utils.get_module_qualname_from_path(os.__file__)
        self.assertEqual('os', name)

        # This will fail because of magic for os.path. Not sure how to fix.
        # name = p_utils.get_module_qualname_from_path(os.path.__file__)
        # self.assertEqual(name, 'os.path')

    def test_get_module_qualname_from_path_invalid_path(self):
        '''Test get_module_qualname_from_path with invalid path.'''

        name = p_utils.get_module_qualname_from_path('/a/b/c/d/e.py')
        self.assertEqual('e', name)

    def test_get_module_qualname_from_path_dir(self):
        '''Test get_module_qualname_from_path with dir path.'''

        self.assertRaises(p_utils.InvalidModulePath,
                          p_utils.get_module_qualname_from_path, '/tmp/')

    def test_namespace_path_join(self):
        p = p_utils.namespace_path_join('base1.base2', 'name')
        self.assertEqual('base1.base2.name', p)

    def test_namespace_path_split(self):
        (head, tail) = p_utils.namespace_path_split('base1.base2.name')
        self.assertEqual('base1.base2', head)
        self.assertEqual('name', tail)

    def test_get_call_name1(self):
        '''Gets a qualified call name.'''
        tree = ast.parse('a.b.c.d(x,y)').body[0].value
        name = p_utils.get_call_name(tree, {})
        self.assertEqual('a.b.c.d', name)

    def test_get_call_name2(self):
        '''Gets qualified call name and resolves aliases.'''
        tree = ast.parse('a.b.c.d(x,y)').body[0].value

        name = p_utils.get_call_name(tree, {'a': 'alias.x.y'})
        self.assertEqual('alias.x.y.b.c.d', name)

        name = p_utils.get_call_name(tree, {'a.b': 'alias.x.y'})
        self.assertEqual('alias.x.y.c.d', name)

        name = p_utils.get_call_name(tree, {'a.b.c.d': 'alias.x.y'})
        self.assertEqual('alias.x.y', name)

    def test_get_call_name3(self):
        '''Getting name for a complex call.'''
        tree = ast.parse('a.list[0](x,y)').body[0].value
        name = p_utils._get_attr_qual_name(tree, {})
        self.assertEqual('', name)
        # TODO(ljfisher) At best we might be able to get:
        # self.assertEqual(name, 'a.list[0]')

    def test_path_for_function(self):
        path = p_utils.get_path_for_function(p_utils.get_path_for_function)
        self.assertEqual(path, p_utils.__file__)

    def test_path_for_function_no_file(self):
        self.assertIsNone(p_utils.get_path_for_function(sys.settrace))

    def test_path_for_function_no_module(self):
        self.assertIsNone(p_utils.get_path_for_function(1))

    def test_escaped_representation_simple(self):
        res = p_utils.escaped_bytes_representation(b"ascii")
        self.assertEqual(res, b"ascii")

    def test_escaped_representation_valid_not_printable(self):
        res = p_utils.escaped_bytes_representation(b"\u0000")
        self.assertEqual(res, b"\\x00")

    def test_escaped_representation_invalid(self):
        res = p_utils.escaped_bytes_representation(b"\uffff")
        self.assertEqual(res, b"\\uffff")

    def test_escaped_representation_mixed(self):
        res = p_utils.escaped_bytes_representation(b"ascii\u0000\uffff")
        self.assertEqual(res, b"ascii\\x00\\uffff")

    def test_deepgetattr(self):
        a = type('', (), {})
        a.b = type('', (), {})
        a.b.c = type('', (), {})
        a.b.c.d = 'deep value'
        a.b.c.d2 = 'deep value 2'
        a.b.c.e = 'a.b.c'
        self.assertEqual('deep value', p_utils.deepgetattr(a.b.c, 'd'))
        self.assertEqual('deep value 2', p_utils.deepgetattr(a.b.c, 'd2'))
        self.assertEqual('a.b.c', p_utils.deepgetattr(a.b.c, 'e'))
        self.assertEqual('deep value', p_utils.deepgetattr(a, 'b.c.d'))
        self.assertEqual('deep value 2', p_utils.deepgetattr(a, 'b.c.d2'))
        self.assertRaises(AttributeError, p_utils.deepgetattr, a.b, 'z')

    def test_parse_ini_file(self):

        tests = [{'content': "[panther]\nexclude=/abc,/def",
                  'expected': {'exclude': '/abc,/def'}},

                 {'content': '[Blabla]\nsomething=something',
                  'expected': None}]

        with tempfile.NamedTemporaryFile('r+') as t:
            for test in tests:
                f = open(t.name, 'w')
                f.write(test['content'])
                f.close()

                self.assertEqual(p_utils.parse_ini_file(t.name),
                                 test['expected'])
    
    def test_extract_name_space(self):

        def test_name_space(code, name_list):
            json_program = esprima.parse(code)
            ast_program =  visitor.objectify(json_program.to_dict())

            call_expression = ast_program.body[0].expression
            name_space = p_utils.extract_name_space(call_expression)
            self.assertSequenceEqual(name_space, name_list)
        
        test_name_space('x()',['*x'])
        test_name_space('x.y.z()',['*x','*y','*z'])
        test_name_space('x[y][z]()',['*x', '?Identifier', '?Identifier'])
        test_name_space('x[y][z.j]() ',['*x','?Identifier','?MemberExpression'])
        test_name_space("x['y'][3]()",['*x','*y','*3'])
        test_name_space("x['y'][3+2]()",['*x','*y','?BinaryExpression'])
        test_name_space('x[y()][z()]()',['*x','?CallExpression','?CallExpression'])
        test_name_space('[].x()',['?ArrayExpression','*x'])
        test_name_space("[]['x']()",['?ArrayExpression','*x'])
        test_name_space('[][x]() ',['?ArrayExpression','?Identifier'])
        test_name_space("''.x()",['?Literal','*x'])
        test_name_space("''['x']()",['?Literal','*x'])
        test_name_space("''[x]()",['?Literal','?Identifier'])
        test_name_space("fn()()",['?CallExpression'])
        test_name_space("(x=1)()",['?AssignmentExpression'])
        test_name_space("Identifier.Identifier()",['*Identifier','*Identifier'])

        
