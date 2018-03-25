from panther.core import config
from panther.core import meta_ast
from panther.core import metrics
from panther.core import node_visitor
from panther.core import test_set
from panther.core.tracer.file_extractor import FileExtractor
from panther.core import utils
from panther.core.visitor import CallExpression


class Diver(object):
    def __init__(self, routes):
        self.routes = routes
        self.extractor = FileExtractor()

    def find(self, function):
        '''Finds and returns functions that are called in a given function.
        If the function name is an string identifier it looks for a function
        in the same document. If the caller is a member expression like
        module.fn() it looks for the module in the require call and if it can
        resolve it goes to the referenced file and fetches the function.
        '''
        file_path = function.file_path
        function_list = []
        for node in function.node.traverse():
            function = None

            # Track call expressions
            if isinstance(node, CallExpression):
                call_expression = node

                # If we have match of an identifier function call like fn()
                if utils.match_name_space(call_expression, ['*']):
                    identifier = utils.extract_name_space(
                        call_expression)[0][1:]
                    function = self.extractor.try_match_function(
                        file_path, identifier)
                # Check whether we have a call like module.fn()
                elif utils.match_name_space(call_expression, ['*', '*']):
                    name_space = utils.extract_name_space(call_expression)
                    module_name = name_space[0][1:]
                    identifier = name_space[1][1:]
                    function = self.extractor.try_fetch_function(
                        file_path, module_name, identifier)
            if function:
                function_list.append(function)

        return function_list

    def test(self, file_path, node):
        '''It tests a given function node with plugins
        and returns test results.
        '''
        nv = node_visitor.PantherNodeVisitor(
            file_path, meta_ast.PantherMetaAst(),
            test_set.PantherTestSet(config, profile=None),
            True,
            set(),
            metrics.Metrics())
        nv.generic_visit(node)
        # TODO(izel): Do something with results.
        # if nv.tester.results:
        #     print(nv.tester.results[0].__dict__)

        # print(nv.scores)
        return nv.tester.results

    def dive_all(self, file_path, depth=1):
        '''For all entry function in routes dives for the vulnerabilities.'''
        for route in self.routes:
            for function in route.entry_point_functions:
                self.dive(function, [route], depth)

    def dive(self, function, stack_trace, depth):
        '''It recursively searches for vulnerabilities.'''
        depth -= 1
        stack_trace.append(function)
        test_result = self.test(function.file_path, function.node)
        if test_result:
            print('\n\nVulnerability Detected!\n\n' +
                  '\n----------------\n'.join(map(repr, stack_trace)))
        else:
            if depth == 0:
                print('Path search finished but nothing found.', stack_trace)
            else:
                other_functions = self.find(function)
                if other_functions:
                    for function in other_functions:
                        self.dive(function, stack_trace, depth)
