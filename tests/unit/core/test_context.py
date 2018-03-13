# -*- coding:utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

import mock
import testtools

from panther.core import context


class ContextTests(testtools.TestCase):

    def test_context_create(self):
        ref_context = mock.Mock()
        new_context = context.Context(context_object=ref_context)
        self.assertEqual(ref_context, new_context._context)

        new_context = context.Context()
        self.assertIsInstance(new_context._context, dict)

    def test_repr(self):
        ref_object = dict(spam='eggs')
        expected_repr = '<Context {}>'.format(ref_object)
        new_context = context.Context(context_object=ref_object)
        self.assertEqual(expected_repr, repr(new_context))

    def test_node(self):
        expected_node = 'spam'
        ref_context = dict(node=expected_node)
        new_context = context.Context(context_object=ref_context)
        self.assertEqual(expected_node, new_context.node)

        new_context = context.Context()
        self.assertIsNone(new_context.node)
