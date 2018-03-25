from panther.core import (config, meta_ast, metrics, node_visitor, test_set,
                          utils)
from panther.core.visitor import CallExpression
from panther.core.tracer.file_extractor import FileExtractor


class Diver(object):
    def __init__(self, routes):
        self.routes = routes
        self.extractor = FileExtractor()

    def find(self, function):
        file_path = function.file_path
        function_list = []
        for node in function.node.traverse():
            function = None
            if isinstance(node, CallExpression):
                call_expression = node
                if utils.match_name_space(call_expression, ['*']):
                    identifier = utils.extract_name_space(
                        call_expression)[0][1:]
                    function = self.extractor.try_match_function(
                        file_path, identifier)
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
        nv = node_visitor.PantherNodeVisitor(
            file_path, meta_ast.PantherMetaAst(), test_set.PantherTestSet(config, profile=None), True, set(), metrics.Metrics())
        nv.generic_visit(node)
        # if nv.tester.results:
        #     print(nv.tester.results[0].__dict__)

        # print(nv.scores)
        return nv.tester.results

    def dive_all(self, file_path, depth=1):
        for route in self.routes:
            for function in route.entry_point_functions:  
                self.dive(function, [route], depth)

    def dive(self, function, stack_trace, depth):
        depth -= 1
        stack_trace.append(function)
        test_result = self.test(function.file_path, function.node)
        if test_result:
            print('\n\nVULNERABILITY DETECTED!\n\n' + '\n----------------\n'.join(map(repr,stack_trace)))
        else:
            if depth == 0:
                print('I AM FINISHED BUT COULDNT FIND:(', stack_trace)
            else:
                other_functions = self.find(function)
                if other_functions:
                    for function in other_functions:
                        self.dive(function, stack_trace, depth)
