# -*- coding:utf-8 -*-

import logging
import operator

from panther.core import constants
from panther.core.pyesprima import esprima
from panther.core import tester as p_tester
from panther.core import utils as p_utils
from panther.core import visitor

LOG = logging.getLogger(__name__)


class PantherNodeVisitor(object):
    def __init__(self, fname, metaast, testset,
                 debug, nosec_lines, metrics):
        self.debug = debug
        self.nosec_lines = nosec_lines
        self.seen = 0
        self.scores = {
            'SEVERITY': [0] * len(constants.RANKING),
            'CONFIDENCE': [0] * len(constants.RANKING)
        }
        self.depth = 0
        self.fname = fname
        self.metaast = metaast
        self.testset = testset
        self.tester = p_tester.PantherTester(
            self.testset, self.debug, nosec_lines)
        # in some cases we can't determine a qualified name
        try:
            self.namespace = p_utils.get_module_qualname_from_path(fname)
        except p_utils.InvalidModulePath:
            LOG.info('Unable to find qualified name for module: %s',
                     self.fname)
            self.namespace = ""
        LOG.debug('Module qualified name: %s', self.namespace)
        self.metrics = metrics

    def pre_visit(self, node):
        self.context = {}

        if self.debug:
            self.metaast.add_node(node, '', self.depth)

        if hasattr(node, 'loc'):
            lineno = node.loc['start']['line']
            self.context['lineno'] = lineno
            if lineno in self.nosec_lines:
                LOG.debug("skipped, nosec")
                self.metrics.note_nosec(lineno)
                return False

        self.context['node'] = node
        self.context['linerange'] = p_utils.linerange_fix(node)
        self.context['filename'] = self.fname

        self.seen += 1
        LOG.debug("entering: %s %s [%s]", hex(id(node)), type(node),
                  self.depth)
        self.depth += 1
        LOG.debug(self.context)
        return True

    def visit(self, node):
        # TODO(Yhnlvy): customize visitor based on node type
        name = node.__class__.__name__
        method = 'visit_' + name
        visitor = getattr(self, method, None)
        if visitor is not None:
            visitor(node)
        else:
            self.update_scores(self.tester.run_tests(self.context, name))

    def post_visit(self, node):
        self.depth -= 1
        LOG.debug("%s\texiting : %s", self.depth, hex(id(node)))

    def generic_visit(self, node):
        """Drive the visitor."""
        for n in visitor.objectify(node).traverse():
            if self.pre_visit(n):
                self.visit(n)
                self.post_visit(n)

    def update_scores(self, scores):
        '''Score updater

        Since we moved from a single score value to a map of scores per
        severity, this is needed to update the stored list.
        :param score: The score list to update our scores with
        '''
        # we'll end up with something like:
        # SEVERITY: {0, 0, 0, 10}  where 10 is weighted by finding and level
        for score_type in self.scores:
            self.scores[score_type] = list(map(
                operator.add, self.scores[score_type], scores[score_type]
            ))

    def process(self, data):
        '''Main process loop

        Build and process the AST
        :param lines: lines code to process
        :return score: the aggregated score for the current file
        '''
        data = p_utils.clean_code(data)
        f_ast = esprima.parse(data, {'loc': True})
        self.generic_visit(f_ast.to_dict())
        return self.scores
